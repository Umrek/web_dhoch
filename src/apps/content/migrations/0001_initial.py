import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Page",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "key",
                    models.CharField(
                        choices=[
                            ("home-hero", "Úvod: hlavní text"),
                            ("home-intro", "Úvod: představení"),
                            ("about-history", "O kapele: historie"),
                            ("about-style", "O kapele: hudební styl"),
                            ("about-current", "O kapele: současná podoba"),
                            ("ochrana-osobnich-udaju", "Ochrana osobních údajů"),
                            ("cookies", "Cookies"),
                            ("provozovatel", "Provozovatel webu"),
                            ("prohlaseni-o-pristupnosti", "Prohlášení o přístupnosti"),
                            ("bezpecnost", "Bezpečnostní kontakt"),
                            ("odstraneni-fotografie", "Odstranění fotografie"),
                        ],
                        max_length=40,
                        unique=True,
                        verbose_name="klíč",
                    ),
                ),
                ("title", models.CharField(max_length=160, verbose_name="nadpis")),
                ("intro", models.TextField(blank=True, verbose_name="úvod")),
                (
                    "body",
                    models.TextField(
                        blank=True,
                        help_text="Prostý text; odstavce oddělte prázdným řádkem.",
                        verbose_name="text",
                    ),
                ),
                (
                    "needs_legal_review",
                    models.BooleanField(
                        default=False,
                        help_text="Zobrazí veřejné upozornění, že text není finální.",
                        verbose_name="vyžaduje právní kontrolu",
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="upraveno")),
            ],
            options={"verbose_name": "stránka", "verbose_name_plural": "stránky", "ordering": ["key"]},
        ),
        migrations.CreateModel(
            name="SiteSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "band_name",
                    models.CharField(
                        default="Dechová hudba Oderské chasy", max_length=120, verbose_name="název kapely"
                    ),
                ),
                ("contact_email", models.EmailField(blank=True, max_length=254, verbose_name="kontaktní e-mail")),
                ("contact_phone", models.CharField(blank=True, max_length=40, verbose_name="kontaktní telefon")),
                ("contact_address", models.TextField(blank=True, verbose_name="kontaktní adresa")),
                ("operator_name", models.CharField(blank=True, max_length=200, verbose_name="provozovatel")),
                ("operator_details", models.TextField(blank=True, verbose_name="údaje o provozovateli")),
            ],
            options={
                "verbose_name": "nastavení webu",
                "verbose_name_plural": "nastavení webu",
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("pk", 1)),
                        name="content_sitesettings_singleton",
                        violation_error_message="Nastavení webu může existovat jen jednou.",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="Announcement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=160, verbose_name="nadpis")),
                ("body", models.TextField(verbose_name="text")),
                (
                    "published_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="zveřejněno od"),
                ),
                ("expires_at", models.DateTimeField(blank=True, null=True, verbose_name="platí do")),
                ("is_active", models.BooleanField(default=True, verbose_name="aktivní")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="vytvořeno")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="autor",
                    ),
                ),
            ],
            options={
                "verbose_name": "interní oznámení",
                "verbose_name_plural": "interní oznámení",
                "ordering": ["-published_at"],
                "indexes": [models.Index(fields=["is_active", "published_at"], name="content_ann_active_idx")],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("expires_at__isnull", True), ("expires_at__gt", models.F("published_at")), _connector="OR"),
                        name="content_announcement_expires_after_publish",
                        violation_error_message="Konec platnosti musí být po začátku zveřejnění.",
                    )
                ],
            },
        ),
    ]
