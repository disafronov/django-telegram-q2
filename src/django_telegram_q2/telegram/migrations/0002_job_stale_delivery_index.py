from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("telegram", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="job",
            index=models.Index(
                condition=models.Q(
                    delivery_error__isnull=True,
                    delivery_finished_at__isnull=True,
                    delivery_started_at__isnull=False,
                ),
                fields=["delivery_started_at"],
                name="tg_job_stale_delivery_idx",
            ),
        ),
    ]
