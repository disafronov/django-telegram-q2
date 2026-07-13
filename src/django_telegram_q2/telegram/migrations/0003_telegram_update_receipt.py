import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("telegram", "0002_job_stale_delivery_index"),
    ]

    operations = [
        migrations.CreateModel(
            name="TelegramUpdateReceipt",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("update_id", models.BigIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "bot",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="telegram.bot",
                    ),
                ),
            ],
            options={
                "verbose_name": "Telegram Update Receipt",
                "verbose_name_plural": "Telegram Update Receipts",
                "db_table": "telegram_updatereceipt",
            },
        ),
        migrations.AddConstraint(
            model_name="telegramupdatereceipt",
            constraint=models.UniqueConstraint(
                fields=("bot", "update_id"),
                name="tg_uniq_update_receipt_per_bot",
            ),
        ),
    ]
