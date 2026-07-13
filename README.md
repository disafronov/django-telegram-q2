# django-telegram-q2

A reusable Django app that turns a Telegram bot into a durable, queue-backed
pipeline: inbound messages are buffered, turned into `Job` records, processed by
a worker you supply, and the result is delivered back to the chat — all driven by
[django-q2](https://github.com/django-q2/django-q2) task scheduling.

```text
Telegram ──► intake (webhook or polling) ──► IntakeBuffer (debounce)
                                                   │
                                                   ▼
                                                Job ──► processing worker (your code)
                                                   │                 │
                                                   │                 ▼
                                                   │            raw_output / error
                                                   ▼                 │
                                          telegram_deliver ◄────────┘
                                                   │
                                                   ▼
                                              Telegram
```

## Features

- **At-least-once, resumable pipeline.** Every message becomes a `Job` with
  explicit `processing_*` / `delivery_*` timestamps and database-level
  check constraints, so a crashed worker or dropped task is safe to retry.
- **Webhook *and* long-polling ingest.** `telegram_setup` heals/registers the
  webhook and transparently falls back to polling when Telegram reports errors
  or the public `BASE_URL` is unavailable. The two never race (a `409` from
  Telegram is tolerated).
- **Message debouncing.** Consecutive messages in the same chat within
  `TELEGRAM_INTAKE_DEBOUNCE_SECONDS` are concatenated into a single `Job`, so a
  multi-line thought is processed as one unit.
- **Encrypted secrets at rest.** Bot API tokens and webhook secrets are stored
  with deterministic AES-SIV encryption (`FIELD_ENCRYPTION_KEY`), while still
  allowing exact-match lookups.
- **Shipped admin + migrations.** `Bot`/`Job`/`IntakeBuffer` are registered with
  the admin, including "retry job", "retry delivery" and "rotate webhook secret"
  actions. Migrations are included.
- **Zero worker assumptions.** The package owns transport and scheduling; you
  implement `process()` and point `Q2_PROCESSING_FUNC` at it.

## Requirements

- Python **3.11**, **3.12**, **3.13**, or **3.14**
- Django **>= 5.2, < 6.0**
- django-q2 **>= 1.0, < 2.0** (and its broker — Redis/ORM/…)
- `cryptography` and `httpx` (declared as dependencies)
- **PostgreSQL recommended** for production (the pipeline relies on
  `SELECT … SKIP LOCKED`; SQLite works for local development and tests).

## Installation

```console
uv add django-telegram-q2
# or
pip install django-telegram-q2
```

## Quick start

### 1. Apps and URLs

```python
# settings.py
INSTALLED_APPS = [
    # … Django apps …
    "django_q",                       # django-q2
    "django_telegram_q2.telegram",    # this app (app label: "telegram")
]

# urls.py
from django.urls import include, path

urlpatterns = [
    path("", include("django_telegram_q2.telegram.urls")),  # exposes /webhook/
]
```

The webhook endpoint is exposed at `/webhook/` (no `app_name` namespace).

### 2. Configure django-q2

The package schedules its work through django-q2, so a `Q_CLUSTER` config is
required. See the django-q2 docs for broker options (Redis/ORM/etc.) and run a
cluster (`manage.py qcluster`).

### 3. Required settings

```python
import os

# 32-byte key, hex-encoded (64 hex chars).
# Generate: python -c "import secrets; print(secrets.token_bytes(32).hex())"
os.environ["FIELD_ENCRYPTION_KEY"] = "…64-hex-chars…"

# Public base URL used to register webhooks. Leave empty to use polling only.
BASE_URL = "https://bot.example.com"

# Processing function — dotted path to a callable taking one int (job_pk).
Q2_PROCESSING_FUNC = "myproject.workers.process_job"

# Managed Q2 schedule intervals (in minutes).
Q2_TELEGRAM_SETUP_MINUTES = 5
Q2_TELEGRAM_INGEST_MINUTES = 1
Q2_TELEGRAM_DELIVER_MINUTES = 1
Q2_TELEGRAM_INTAKE_FLUSH_MINUTES = 1
Q2_PROCESSING_MINUTES = 1

# Webhook health management.
WEBHOOK_COOLDOWN_SECONDS = 300
WEBHOOK_FALLBACK_PENDING_THRESHOLD = 100

# How long a claimed-but-unfinished Job stays stuck before being reset (seconds).
Q2_PROCESSING_STALE_JOB_SECONDS = 3600

# Emoji sent to acknowledge receipt; empty string disables the reaction.
TELEGRAM_ACK_REACTION = "🤖"
```

### 4. Migrate

```console
python manage.py migrate
```

Migrations for the `telegram` app are shipped, so no `makemigrations` is needed
for the package models.

## Models

| Model | Purpose |
| --- | --- |
| `Bot` | A Telegram bot identity: encrypted `telegram_api_token`, `webhook_secret`, poll `telegram_update_offset`, webhook state. |
| `Job` | One pipeline execution: `raw_input` → (`raw_output` \| `processing_error`) → delivery state. Carries DB-level check constraints and partial indexes for queue queries. |
| `IntakeBuffer` | Mutable accumulator of consecutive chat messages before a `Job` is created; one open buffer per `bot`+`chat`. |

`Job.objects` is a `JobQuerySet` with `ready_for_processing()`,
`stale_processing(cutoff)` and `ready_for_delivery()` for queue queries.

## How the pipeline runs

1. **Intake.** Either the `/webhook/` view (when a webhook is registered) or
   `telegram_ingest` (long-polling) calls `accept_telegram_message`. Messages
   within `TELEGRAM_INTAKE_DEBOUNCE_SECONDS` of the last one are appended to the
   open `IntakeBuffer`; otherwise the buffer is flushed into a `Job` first.
2. **Processing.** A `post_save` signal on the new `Job` enqueues
   `Q2_PROCESSING_FUNC(job_pk)`. Your worker runs `process()`, stores the result
   on the `Job`, and a second signal enqueues `telegram_deliver`.
3. **Delivery.** `telegram_deliver` sends `raw_output` back to the chat as a
   text document (format auto-detected as HTML/Markdown/plain text), or the
   `processing_error` as a plain message. On failure it records `delivery_error`,
   marks the delivery attempt as finished, and re-raises. Retrying remains an
   explicit admin action because Telegram sends are not idempotent.

`telegram_setup`, `telegram_ingest`, `telegram_deliver`,
`telegram_flush_intake_buffers` and your processing function are all managed
**Q2 schedules** created on `post_migrate` and protected from admin drift (any
edit is reverted, any delete is recreated) via `pre_save`/`post_delete`
handlers.

## Implementing a worker

Subclass `django_telegram_q2.telegram.worker.Worker` and implement `process()`:

```python
# myproject/workers.py
from django_telegram_q2.telegram.worker import Worker


class EchoWorker(Worker):
    # Optional: restrict which Jobs are polled, and what to select_related.
    poll_filters: dict = {}
    poll_select_related: tuple[str, ...] = ()
    pk_select_related: tuple[str, ...] = ()

    def process(self, *, bot_id: int, raw_input: str) -> tuple[str | None, str | None]:
        # Return (result, None) on success,
        # return (None, "error message") on a handled error (no re-raise),
        # or raise on an unexpected failure (re-raised by run()).
        return f"You said: {raw_input}", None


def process_job(job_pk: int) -> None:
    EchoWorker().run(job_pk)
```

```python
# settings.py
Q2_PROCESSING_FUNC = "myproject.workers.process_job"
```

`Worker.run` handles Job selection, locking (`skip_locked`), transaction
management, stale-Job reset, and persisting the outcome.

## Webhook vs polling

- Set `BASE_URL` to a publicly reachable HTTPS URL. `telegram_setup` registers
  the webhook (with the per-bot `webhook_secret` sent as the
  `X-Telegram-Bot-Api-Secret-Token` header, which the view verifies).
- If `BASE_URL` is empty, or Telegram reports a webhook error / too many pending
  updates, the app deletes the webhook and falls back to `telegram_ingest`
  long-polling. After `WEBHOOK_COOLDOWN_SECONDS` it retries webhook
  registration.
- The view rejects any request without a matching secret header with `404`.

## Settings reference

| Setting | Required | Default | Description |
| --- | --- | --- | --- |
| `Q2_PROCESSING_FUNC` | yes | — | Dotted path to the processing entry function `(job_pk: int) -> None`. |
| `Q2_TELEGRAM_SETUP_MINUTES` | yes | — | Interval for `telegram_setup` (webhook health). |
| `Q2_TELEGRAM_INGEST_MINUTES` | yes | — | Interval for `telegram_ingest` (polling). |
| `Q2_TELEGRAM_DELIVER_MINUTES` | yes | — | Interval for `telegram_deliver` (drain deliveries). |
| `Q2_TELEGRAM_INTAKE_FLUSH_MINUTES` | yes | — | Interval for the intake-buffer safety flush. |
| `Q2_PROCESSING_MINUTES` | yes | — | Interval for your processing schedule. |
| `WEBHOOK_COOLDOWN_SECONDS` | yes | — | Quiet period after falling back to polling before retrying webhook. |
| `WEBHOOK_FALLBACK_PENDING_THRESHOLD` | yes | — | `pending_update_count` above which the webhook is considered unhealthy. |
| `Q2_PROCESSING_STALE_JOB_SECONDS` | yes | — | Age after which a claimed-but-unfinished Job is reset for retry. |
| `TELEGRAM_ACK_REACTION` | yes | — | Emoji acknowledgement; `""` disables it. |
| `BASE_URL` | no | `""` | Public base URL for webhook registration (empty ⇒ polling only). |
| `TELEGRAM_INTAKE_DEBOUNCE_SECONDS` | no | `10` | Window for grouping consecutive chat messages into one `Job`. |

| Env var | Required | Description |
| --- | --- | --- |
| `FIELD_ENCRYPTION_KEY` | yes | 32-byte (16/24/32 accepted) key, hex-encoded, for AES-SIV field encryption. |

## Development

This repository ships its own dev tooling:

```console
make install      # install deps + pre-commit hooks
make lint         # black, isort, flake8, mypy, bandit
make test         # pytest with 100% branch coverage
make dead-code    # vulture
make audit        # pip-audit
make all          # lint → test → dead-code
```

Tests run against SQLite in-memory by default, and against PostgreSQL when
`DATABASE_HOST` is set (e.g. via `compose.yml`).

## License

Apache-2.0. See [LICENSE](LICENSE).
