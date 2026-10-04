import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import apps.common.storage


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Album",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=160, verbose_name="název")),
                ("slug", models.SlugField(max_length=100, unique=True, verbose_name="adresa (slug)")),
                ("description", models.TextField(blank=True, verbose_name="popis")),
                ("happened_on", models.DateField(blank=True, null=True, verbose_name="datum akce")),
                ("is_published", models.BooleanField(default=False, verbose_name="zveřejněno")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="vytvořeno")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="upraveno")),
            ],
            options={
                "verbose_name": "album",
                "verbose_name_plural": "alba",
                "ordering": ["-happened_on", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="GalleryImage",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "image",
                    models.FileField(
                        editable=False,
                        max_length=200,
                        storage=apps.common.storage.gallery_storage,
                        upload_to="",
                        verbose_name="obrázek",
                    ),
                ),
                (
                    "thumbnail",
                    models.FileField(
                        editable=False,
                        max_length=200,
                        storage=apps.common.storage.gallery_storage,
                        upload_to="",
                        verbose_name="náhled",
                    ),
                ),
                ("width", models.PositiveIntegerField(default=0, editable=False)),
                ("height", models.PositiveIntegerField(default=0, editable=False)),
                (
                    "alt_text",
                    models.CharField(
                        help_text="Stručný popis obsahu fotografie pro čtečky obrazovky (povinné).",
                        max_length=250,
                        verbose_name="alternativní text",
                    ),
                ),
                ("caption", models.CharField(blank=True, max_length=250, verbose_name="popisek")),
                ("position", models.PositiveIntegerField(default=0, verbose_name="pořadí")),
                ("is_published", models.BooleanField(default=True, verbose_name="zveřejněno")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="nahráno")),
                (
                    "album",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="images",
                        to="gallery.album",
                        verbose_name="album",
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
                    ),
                ),
            ],
            options={
                "verbose_name": "fotografie",
                "verbose_name_plural": "fotografie",
                "ordering": ["album", "position", "created_at"],
                "indexes": [models.Index(fields=["album", "is_published"], name="gallery_image_album_idx")],
            },
        ),
    ]
