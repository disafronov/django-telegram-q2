"""Test settings for django-telegram-q2 standalone testing."""

import os

os.environ["FIELD_ENCRYPTION_KEY"] = (
    "0" * 64  # 256-bit key hex for AES-SIV, deterministic for tests
)

SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = True
ALLOWED_HOSTS = ["*"]
ROOT_URLCONF = "tests.urls"

WEBHOOK_COOLDOWN_SECONDS = 300
WEBHOOK_FALLBACK_PENDING_THRESHOLD = 5
TELEGRAM_ACK_REACTION = "\U0001f914"
TELEGRAM_INTAKE_DEBOUNCE_SECONDS = 10

Q2_PROCESSING_FUNC = "tests.dummy_processing.dummy_processing"
Q2_PROCESSING_STALE_JOB_SECONDS = 3600
Q2_DELIVERY_STALE_JOB_SECONDS = 3600
Q2_SUCCESS_RETENTION_SECONDS = 86400
Q2_TELEGRAM_SETUP_MINUTES = 1
Q2_TELEGRAM_INGEST_MINUTES = 1
Q2_TELEGRAM_DELIVER_MINUTES = 1
Q2_TELEGRAM_INTAKE_FLUSH_MINUTES = 1
Q2_PROCESSING_MINUTES = 1
Q2_SUCCESS_CLEANUP_MINUTES = 60

if os.getenv("DATABASE_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": os.getenv("DATABASE_HOST", "localhost"),
            "PORT": os.getenv("DATABASE_PORT", "5432"),
            "NAME": os.getenv("DATABASE_NAME", "database"),
            "USER": os.getenv("DATABASE_USER", "user"),
            "PASSWORD": os.getenv("DATABASE_PASSWORD", "password"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.admin",
    "django.contrib.staticfiles",
    "django_q",
    "django_telegram_q2.telegram",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

STATIC_URL = "/static/"

USE_TZ = True
TIME_ZONE = "UTC"

Q_CLUSTER = {
    "name": "test",
    "workers": 1,
    "timeout": 30,
    "retry": 35,
    "queue_limit": 10,
    "bulk": 1,
    "orm": "default",
    "catch_up": False,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
    },
}
