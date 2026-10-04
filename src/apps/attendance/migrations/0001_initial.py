import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("events", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AttendanceResponse",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[("ano", "Přijdu"), ("ne", "Nepřijdu"), ("mozna", "Zatím nevím")],
                        max_length=6,
                        verbose_name="odpověď",
                    ),
                ),
                ("note", models.CharField(blank=True, max_length=300, verbose_name="poznámka")),
                ("responded_at", models.DateTimeField(auto_now_add=True, verbose_name="poprvé odpovězeno")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="naposledy změněno")),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attendance_responses",
                        to="events.event",
                        verbose_name="akce",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attendance_responses",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="muzikant",
                    ),
                ),
            ],
            options={
                "verbose_name": "odpověď o docházce",
                "verbose_name_plural": "odpovědi o docházce",
                "ordering": ["event__starts_at", "user__email"],
                "indexes": [models.Index(fields=["event", "status"], name="attendance_event_status_idx")],
                "constraints": [
                    models.UniqueConstraint(fields=("event", "user"), name="attendance_unique_event_user")
                ],
            },
        ),
    ]
