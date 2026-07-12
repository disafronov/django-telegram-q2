"""AppConfig for django_telegram_q2.telegram pipeline schedules."""

from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_delete, post_migrate, pre_save

from ..common.schedules import (
    make_recreate_handler,
    make_restore_handler,
    make_sync_handler,
)

MANAGED_SCHEDULES = (
    {
        "name": "django_telegram_q2.telegram.setup",
        "func": "django_telegram_q2.telegram.tasks.telegram_setup",
        "minutes": "Q2_TELEGRAM_SETUP_MINUTES",
    },
    {
        "name": "django_telegram_q2.telegram.ingest",
        "func": "django_telegram_q2.telegram.tasks.telegram_ingest",
        "minutes": "Q2_TELEGRAM_INGEST_MINUTES",
    },
    {
        "name": "django_telegram_q2.telegram.deliver",
        "func": "django_telegram_q2.telegram.tasks.telegram_deliver",
        "minutes": "Q2_TELEGRAM_DELIVER_MINUTES",
    },
    {
        "name": "django_telegram_q2.telegram.intake_flush",
        "func": "django_telegram_q2.telegram.tasks.telegram_flush_intake_buffers",
        "minutes": "Q2_TELEGRAM_INTAKE_FLUSH_MINUTES",
    },
    {
        "name": "django_telegram_q2.processing",
        "func": settings.Q2_PROCESSING_FUNC,
        "minutes": "Q2_PROCESSING_MINUTES",
    },
)


class TelegramConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_telegram_q2.telegram"
    label = "telegram"

    def ready(self) -> None:
        # post_migrate (not ready()) avoids DB queries on every manage.py command
        post_migrate.connect(
            make_sync_handler(MANAGED_SCHEDULES), sender=self, weak=False
        )
        from django_q.models import Schedule

        import django_telegram_q2.telegram.signals  # noqa: F401

        pre_save.connect(
            make_restore_handler(MANAGED_SCHEDULES),
            sender=Schedule,
            dispatch_uid="telegram.protect_managed_q2_schedules",
            weak=False,
        )
        post_delete.connect(
            make_recreate_handler(MANAGED_SCHEDULES),
            sender=Schedule,
            dispatch_uid="telegram.recreate_managed_q2_schedules",
            weak=False,
        )
