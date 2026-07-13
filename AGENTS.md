# Repository Guidelines

## Project Structure & Module Organization

Production code lives under `src/django_telegram_q2/`. The `telegram/` package contains the Django app, including models, migrations, views, queue tasks, and worker logic; shared utilities live in `common/`. Tests are colocated in each package's `tests/` directory and use the top-level `tests/` package for Django settings, URLs, and test helpers. Packaging and tool configuration is centralized in `pyproject.toml`; `compose.yml` provides a local PostgreSQL service. User-facing behavior and configuration belong in `README.md`, with release notes in `CHANGELOG.md`.

## Build, Test, and Development Commands

- `make install`: install the pinned Python version and dependencies with `uv`, then install pre-commit hooks.
- `make format`: apply Black and isort formatting.
- `make lint`: check Black, isort, Flake8, mypy, and Bandit.
- `make test`: run pytest verbosely and write HTML coverage to `htmlcov/`.
- `make dead-code`: scan `src/` with Vulture.
- `make audit`: check installed dependencies for known vulnerabilities with
  `pip-audit`.
- `make all`: run linting, tests, and dead-code checks; use this before opening a PR.
- `docker compose up postgres`: start the optional local PostgreSQL 17 service. Tests otherwise use in-memory SQLite.

## Coding Style & Naming Conventions

Use Python 3.11–3.14 syntax, four-space indentation, and an 88-character line limit. Black and isort define formatting; Flake8 enforces style. Add complete type annotations to production code because mypy rejects untyped and incomplete definitions. Use `snake_case` for functions and modules, `PascalCase` for classes and Django models, and uppercase names for settings/constants. Do not manually edit existing migrations; create a new numbered migration for schema changes.

## Testing Guidelines

Write pytest tests as `test_*.py` with functions named `test_*`, colocated with the relevant package. `pytest-django` loads `tests.settings`. Coverage includes branches and must remain at 100%; cover success, failure, and retry/state-transition paths. Run a focused test with `uv run pytest src/django_telegram_q2/telegram/tests/test_worker.py`, then run `make test` before submission.

## Commit & Pull Request Guidelines

History follows Conventional Commit-style subjects such as `feat:`, `build:`, `ci:`, and scoped forms like `build(deps):`. Keep subjects imperative and focused, and create commits with `git commit --signoff` because the repository enforces DCO sign-off. PRs should explain the behavior change, note configuration or migration impacts, link relevant issues, and include test results. Add screenshots only for admin or other visible UI changes. Update `README.md` when public behavior or configuration changes; update `CHANGELOG.md` only while preparing a release or when explicitly requested.
