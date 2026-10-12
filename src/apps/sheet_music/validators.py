"""Upload validation for sheet music: PDF only, signature-checked, size-limited."""

import logging

from django.conf import settings
from django.core.exceptions import ValidationError

from apps.common.audit import log_security_event
from apps.common.files import extension_of
from apps.common.malware import MalwareDetectedError, MalwareScanFailedError, scan_stream_with_clamd

PDF_SIGNATURE = b"%PDF-"


def scan_pdf_upload(upload) -> None:
    scan_stream_with_clamd(
        upload,
        host=settings.CLAMAV_HOST,
        port=settings.CLAMAV_PORT,
        timeout_seconds=settings.SHEET_MUSIC_SCAN_TIMEOUT_SECONDS,
    )


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
    if not settings.SHEET_MUSIC_SCAN_ENABLED:
        return
    try:
        scan_pdf_upload(upload)
    except MalwareDetectedError:
        log_security_event("sheet_music_upload_blocked_malware", level=logging.ERROR)
        raise ValidationError("Soubor neprošel antivirovou kontrolou.") from None
    except MalwareScanFailedError:
        log_security_event("sheet_music_upload_scan_unavailable", level=logging.ERROR)
        if settings.SHEET_MUSIC_SCAN_FAIL_CLOSED:
            raise ValidationError(
                "Antivirová kontrola je dočasně nedostupná. Zkuste to prosím později."
            ) from None
