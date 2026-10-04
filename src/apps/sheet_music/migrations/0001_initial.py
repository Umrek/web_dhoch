import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import apps.common.storage
import apps.sheet_music.models
import apps.sheet_music.validators

SECTIONS = [
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
    ("partitura", "Partitura (všechny hlasy)"),
]


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Piece",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="název skladby")),
                ("composer", models.CharField(blank=True, max_length=160, verbose_name="skladatel")),
                ("arranger", models.CharField(blank=True, max_length=160, verbose_name="aranžér")),
                ("notes", models.TextField(blank=True, verbose_name="interní poznámka")),
                ("is_archived", models.BooleanField(default=False, verbose_name="archivováno")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="vytvořeno")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="upraveno")),
            ],
            options={"verbose_name": "skladba", "verbose_name_plural": "skladby", "ordering": ["title"]},
        ),
        migrations.CreateModel(
            name="SheetMusicPart",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("section", models.CharField(choices=SECTIONS, max_length=12, verbose_name="hlas / sekce")),
                (
                    "file",
                    models.FileField(
                        max_length=200,
                        storage=apps.common.storage.sheet_music_storage,
                        upload_to=apps.sheet_music.models.part_upload_to,
                        validators=[apps.sheet_music.validators.validate_pdf],
                        verbose_name="soubor PDF",
                    ),
                ),
                (
                    "original_name",
                    models.CharField(blank=True, editable=False, max_length=200, verbose_name="původní název souboru"),
                ),
                ("size_bytes", models.PositiveIntegerField(default=0, editable=False, verbose_name="velikost (B)")),
                (
                    "sha256",
                    models.CharField(blank=True, editable=False, max_length=64, verbose_name="kontrolní součet SHA-256"),
                ),
                ("version", models.PositiveIntegerField(default=1, editable=False, verbose_name="verze")),
                ("is_current", models.BooleanField(default=True, verbose_name="aktuální verze")),
                (
                    "copyright_confirmed",
                    models.BooleanField(
                        default=False,
                        help_text="Noty mohou podléhat autorskému právu. Nahrávejte jen materiály, které smíte sdílet.",
                        verbose_name="potvrzuji, že mám právo noty sdílet uvnitř kapely",
                    ),
                ),
                ("uploaded_at", models.DateTimeField(auto_now_add=True, verbose_name="nahráno")),
                (
                    "piece",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parts",
                        to="sheet_music.piece",
                        verbose_name="skladba",
                    ),
                ),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="nahrál",
                    ),
                ),
            ],
            options={
                "verbose_name": "hlas (noty)",
                "verbose_name_plural": "hlasy (noty)",
                "ordering": ["piece__title", "section", "-version"],
                "indexes": [models.Index(fields=["section", "is_current"], name="sheet_music_section_idx")],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("piece", "section", "version"), name="sheet_music_unique_version"
                    ),
                    models.UniqueConstraint(
                        condition=models.Q(("is_current", True)),
                        fields=("piece", "section"),
                        name="sheet_music_one_current_part",
                    ),
                ],
            },
        ),
    ]
