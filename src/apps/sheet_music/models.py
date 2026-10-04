import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.common.choices import InstrumentSection
from apps.common.storage import sheet_music_storage

from .validators import validate_pdf


def part_upload_to(instance: "SheetMusicPart", filename: str) -> str:
    """Storage name is generated; the user-supplied name never reaches the filesystem."""
    return f"{instance.piece_id}/{uuid.uuid4().hex}.pdf"


class Piece(models.Model):
    title = models.CharField("název skladby", max_length=200)
    composer = models.CharField("skladatel", max_length=160, blank=True)
    arranger = models.CharField("aranžér", max_length=160, blank=True)
    notes = models.TextField("interní poznámka", blank=True)
    is_archived = models.BooleanField("archivováno", default=False)
    created_at = models.DateTimeField("vytvořeno", auto_now_add=True)
    updated_at = models.DateTimeField("upraveno", auto_now=True)

    class Meta:
        verbose_name = "skladba"
        verbose_name_plural = "skladby"
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title


class SheetMusicPart(models.Model):
    """One PDF for one instrument section; the newest is flagged ``is_current``."""

    piece = models.ForeignKey(
        Piece, on_delete=models.CASCADE, related_name="parts", verbose_name="skladba"
    )
    section = models.CharField("hlas / sekce", max_length=12, choices=InstrumentSection.choices)
    file = models.FileField(
        "soubor PDF",
        upload_to=part_upload_to,
        storage=sheet_music_storage,
        validators=[validate_pdf],
        max_length=200,
    )
    original_name = models.CharField("původní název souboru", max_length=200, blank=True, editable=False)
    size_bytes = models.PositiveIntegerField("velikost (B)", default=0, editable=False)
    sha256 = models.CharField("kontrolní součet SHA-256", max_length=64, blank=True, editable=False)
    version = models.PositiveIntegerField("verze", default=1, editable=False)
    is_current = models.BooleanField("aktuální verze", default=True)
    copyright_confirmed = models.BooleanField(
        "potvrzuji, že mám právo noty sdílet uvnitř kapely",
        default=False,
        help_text="Noty mohou podléhat autorskému právu. Nahrávejte jen materiály, které smíte sdílet.",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
        editable=False,
        verbose_name="nahrál",
    )
    uploaded_at = models.DateTimeField("nahráno", auto_now_add=True)

    class Meta:
        verbose_name = "hlas (noty)"
        verbose_name_plural = "hlasy (noty)"
        ordering = ["piece__title", "section", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["piece", "section", "version"], name="sheet_music_unique_version"
            ),
            models.UniqueConstraint(
                fields=["piece", "section"],
                condition=Q(is_current=True),
                name="sheet_music_one_current_part",
            ),
        ]
        indexes = [models.Index(fields=["section", "is_current"], name="sheet_music_section_idx")]

    def __str__(self) -> str:
        return f"{self.piece} – {self.get_section_display()} (v{self.version})"

    def clean(self) -> None:
        super().clean()
        if self._state.adding and not self.copyright_confirmed:
            raise ValidationError(
                {"copyright_confirmed": "Před nahráním je nutné potvrdit právo noty sdílet."}
            )
