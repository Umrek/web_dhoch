"""Sheet-music use cases: versioned upload and audited download."""

from django.db import transaction
from django.db.models import Max

from apps.common.audit import log_admin_event, log_security_event
from apps.common.files import safe_stem, sha256_hexdigest

from .models import Piece, SheetMusicPart


class CopyrightNotConfirmed(Exception):
    pass


@transaction.atomic
def register_upload(part: SheetMusicPart, *, actor) -> SheetMusicPart:
    """Finalize a new (unsaved) part: metadata, next version, retire the previous current one."""
    if not part.copyright_confirmed:
        raise CopyrightNotConfirmed
    upload = part.file.file
    part.original_name = (getattr(upload, "name", "") or part.file.name)[-200:]
    part.size_bytes = upload.size
    part.sha256 = sha256_hexdigest(upload)
    Piece.objects.select_for_update().get(pk=part.piece_id)
    latest = SheetMusicPart.objects.filter(piece=part.piece, section=part.section).aggregate(
        m=Max("version")
    )["m"]
    part.version = (latest or 0) + 1
    SheetMusicPart.objects.filter(piece=part.piece, section=part.section, is_current=True).update(
        is_current=False
    )
    part.is_current = True
    part.uploaded_by = actor
    part.save()
    log_admin_event(
        "sheet_music_uploaded",
        part_id=part.pk,
        piece_id=part.piece_id,
        version=part.version,
        actor_id=str(getattr(actor, "pk", "")),
    )
    return part


def download_filename(part: SheetMusicPart) -> str:
    return f"{safe_stem(part.piece.title, default='noty')}_{part.section}_v{part.version}.pdf"


def log_download(part: SheetMusicPart, user) -> None:
    log_security_event(
        "sheet_music_downloaded", user_id=str(user.pk), part_id=part.pk, piece_id=part.piece_id
    )
