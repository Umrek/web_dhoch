import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="MusicianProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("display_name", models.CharField(max_length=120, verbose_name="jméno")),
                (
                    "section",
                    models.CharField(
                        choices=[
                            ("kapelnik", "Kapelník"),
                            ("kridlovky", "Křídlovky"),
                            ("trubky", "Trubky"),
                            ("klarinety", "Klarinety"),
                            ("tenory", "Tenory"),
                            ("barytony", "Barytony"),
                            ("pozouny", "Pozouny"),
                            ("basy", "Basy"),
                            ("bici", "Bicí"),
                            ("zpev", "Zpěv"),
                        ],
                        max_length=12,
                        verbose_name="sekce",
                    ),
                ),
                ("instrument", models.CharField(blank=True, max_length=80, verbose_name="nástroj")),
                (
                    "public_listing",
                    models.BooleanField(
                        default=False,
                        help_text="Zobrazí se pouze jméno, sekce a nástroj. Souhlas lze kdykoli odvolat.",
                        verbose_name="zobrazit na veřejné stránce kapely",
                    ),
                ),
                (
                    "public_listing_changed_at",
                    models.DateTimeField(
                        blank=True, editable=False, null=True, verbose_name="změna souhlasu se zveřejněním"
                    ),
                ),
                (
                    "phone",
                    models.CharField(
                        blank=True,
                        help_text="Viditelný jen správcům. Nepovinné.",
                        max_length=20,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^\\+?[0-9 ]{9,16}$",
                                "Zadejte telefon ve tvaru 123 456 789 nebo +420 123 456 789.",
                            )
                        ],
                        verbose_name="telefon",
                    ),
                ),
                ("is_active_member", models.BooleanField(default=True, verbose_name="aktivní člen")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="vytvořeno")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="upraveno")),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="musician_profile",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="uživatel",
                    ),
                ),
            ],
            options={
                "verbose_name": "profil muzikanta",
                "verbose_name_plural": "profily muzikantů",
                "ordering": ["section", "display_name"],
                "indexes": [
                    models.Index(fields=["public_listing", "is_active_member"], name="musicians_public_idx")
                ],
            },
        ),
    ]
