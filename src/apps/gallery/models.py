import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse

from apps.common.storage import gallery_storage


class Album(models.Model):
    title = models.CharField("název", max_length=160)
    slug = models.SlugField("adresa (slug)", max_length=100, unique=True)
    description = models.TextField("popis", blank=True)
    happened_on = models.DateField("datum akce", null=True, blank=True)
    is_published = models.BooleanField("zveřejněno", default=False)
    created_at = models.DateTimeField("vytvořeno", auto_now_add=True)
    updated_at = models.DateTimeField("upraveno", auto_now=True)

    class Meta:
        verbose_name = "album"
        verbose_name_plural = "alba"
        ordering = ["-happened_on", "-created_at"]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("gallery:album", kwargs={"slug": self.slug})


class GalleryImage(models.Model):
    """Processed photo. Originals are never stored; EXIF/GPS metadata is stripped on upload."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    album = models.ForeignKey(
        Album, on_delete=models.CASCADE, related_name="images", verbose_name="album"
    )
    image = models.FileField(
        "obrázek", storage=gallery_storage, max_length=200, editable=False
    )
    thumbnail = models.FileField(
        "náhled", storage=gallery_storage, max_length=200, editable=False
    )
    width = models.PositiveIntegerField(default=0, editable=False)
    height = models.PositiveIntegerField(default=0, editable=False)
    alt_text = models.CharField(
        "alternativní text",
        max_length=250,
        help_text="Stručný popis obsahu fotografie pro čtečky obrazovky (povinné).",
    )
    caption = models.CharField("popisek", max_length=250, blank=True)
    position = models.PositiveIntegerField("pořadí", default=0)
    is_published = models.BooleanField("zveřejněno", default=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
        editable=False,
    )
    created_at = models.DateTimeField("nahráno", auto_now_add=True)

    class Meta:
        verbose_name = "fotografie"
        verbose_name_plural = "fotografie"
        ordering = ["album", "position", "created_at"]
        indexes = [models.Index(fields=["album", "is_published"], name="gallery_image_album_idx")]

    def __str__(self) -> str:
        return self.alt_text[:60]
