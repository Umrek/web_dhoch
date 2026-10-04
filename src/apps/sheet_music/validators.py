"""Upload validation for sheet music: PDF only, signature-checked, size-limited."""

from django.conf import settings
from django.core.exceptions import ValidationError

from apps.common.files import extension_of

PDF_SIGNATURE = b"%PDF-"


def validate_pdf(upload) -> None:
    if extension_of(upload.name) != ".pdf":
        raise ValidationError("Povolen je pouze soubor ve formátu PDF.")
    if upload.size > settings.MAX_SHEET_MUSIC_BYTES:
        limit_mb = settings.MAX_SHEET_MUSIC_BYTES // (1024 * 1024)
        raise ValidationError(f"Soubor je příliš velký (maximum {limit_mb} MB).")
    if upload.size == 0:
        raise ValidationError("Soubor je prázdný.")
    position = upload.tell() if hasattr(upload, "tell") else 0
    upload.seek(0)
    header = upload.read(len(PDF_SIGNATURE))
    upload.seek(position)
    if header != PDF_SIGNATURE:
        raise ValidationError("Soubor není platné PDF.")
