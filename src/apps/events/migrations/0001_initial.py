import uuid

import django.db.models.expressions
from django.db import migrations, models

import apps.events.validators


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Event",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("title", models.CharField(max_length=160, verbose_name="název")),
                ("slug", models.SlugField(max_length=100, unique=True, verbose_name="adresa (slug)")),
                (
                    "kind",
                    models.CharField(
                        choices=[("koncert", "Koncert"), ("zkouska", "Zkouška"), ("jina", "Jiná akce")],
                        default="koncert",
                        max_length=10,
                        verbose_name="druh",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("planovano", "Plánováno"),
                            ("potvrzeno", "Potvrzeno"),
                            ("zruseno", "Zrušeno"),
                        ],
                        default="planovano",
                        max_length=10,
                        verbose_name="stav",
                    ),
                ),
                (
                    "is_public",
                    models.BooleanField(
                        default=False,
                        help_text="Zkoušky nelze zveřejnit.",
                        verbose_name="zveřejnit na webu",
                    ),
                ),
                ("starts_at", models.DateTimeField(verbose_name="začátek vystoupení / akce")),
                ("ends_at", models.DateTimeField(blank=True, null=True, verbose_name="konec")),
                ("meeting_time", models.DateTimeField(blank=True, null=True, verbose_name="sraz")),
                ("venue_name", models.CharField(blank=True, max_length=160, verbose_name="místo")),
                (
                    "venue_address",
                    models.CharField(blank=True, max_length=250, verbose_name="adresa místa"),
                ),
                (
                    "map_url",
                    models.URLField(
                        blank=True,
                        help_text="Volitelné; jinak se vytvoří odkaz na OpenStreetMap z adresy.",
                        validators=[apps.events.validators.validate_https_url],
                        verbose_name="odkaz na mapu",
                    ),
                ),
                ("public_description", models.TextField(blank=True, verbose_name="veřejný popis")),
                (
                    "internal_notes",
                    models.TextField(
                        blank=True,
                        help_text="Nikdy se nezobrazují veřejně (oblečení, doprava, repertoár...).",
                        verbose_name="interní pokyny pro muzikanty",
                    ),
                ),
                (
                    "attendance_enabled",
                    models.BooleanField(default=True, verbose_name="sbírat docházku"),
                ),
                (
                    "attendance_deadline",
                    models.DateTimeField(blank=True, null=True, verbose_name="uzávěrka odpovědí"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="vytvořeno")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="upraveno")),
            ],
            options={
                "verbose_name": "akce",
                "verbose_name_plural": "akce",
                "ordering": ["starts_at"],
                "indexes": [
                    models.Index(fields=["starts_at"], name="events_event_starts_idx"),
                    models.Index(fields=["is_public", "starts_at"], name="events_event_public_idx"),
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(
                            ("ends_at__isnull", True),
                            ("ends_at__gt", django.db.models.expressions.F("starts_at")),
                            _connector="OR",
                        ),
                        name="events_event_ends_after_start",
                        violation_error_message="Konec musí být po začátku.",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("meeting_time__isnull", True),
                            ("meeting_time__lte", django.db.models.expressions.F("starts_at")),
                            _connector="OR",
                        ),
                        name="events_event_meeting_before_start",
                        violation_error_message="Sraz nemůže být po začátku.",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("attendance_deadline__isnull", True),
                            ("attendance_deadline__lte", django.db.models.expressions.F("starts_at")),
                            _connector="OR",
                        ),
                        name="events_event_deadline_before_start",
                        violation_error_message="Uzávěrka nemůže být po začátku.",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("is_public", True), ("kind", "zkouska"), _negated=True),
                        name="events_event_rehearsal_not_public",
                        violation_error_message="Zkoušku nelze zveřejnit na veřejném webu.",
                    ),
                ],
            },
        ),
    ]
