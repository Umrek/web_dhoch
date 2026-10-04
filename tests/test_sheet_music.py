"""Sheet music: upload validation, versioning, object-level access, safe delivery."""

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.sheet_music.models import Piece, SheetMusicPart
from apps.sheet_music.services import CopyrightNotConfirmed, register_upload
from apps.sheet_music.validators import validate_pdf

from .conftest import MINIMAL_PDF

pytestmark = pytest.mark.django_db


def pdf(name="Noty.pdf", content=MINIMAL_PDF):
    return SimpleUploadedFile(name, content, content_type="application/pdf")


@pytest.fixture
def piece():
    return Piece.objects.create(title="Škoda lásky", composer="Fiktivní")


def upload(piece, user, *, section="trubky", name="Noty.pdf"):
    part = SheetMusicPart(piece=piece, section=section, copyright_confirmed=True, file=pdf(name))
    return register_upload(part, actor=user)


def test_validator_accepts_real_pdf_header():
    validate_pdf(pdf())


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("noty.exe", MINIMAL_PDF),
        ("noty.pdf", b"MZ\x90\x00 not a pdf"),
        ("noty.pdf", b""),
        ("noty.pdf.php", MINIMAL_PDF),
    ],
)
def test_validator_rejects_bad_files(name, content):
    with pytest.raises(ValidationError):
        validate_pdf(pdf(name, content))


def test_validator_rejects_oversized(settings):
    settings.MAX_SHEET_MUSIC_BYTES = 10
    with pytest.raises(ValidationError):
        validate_pdf(pdf(content=MINIMAL_PDF))


def test_copyright_confirmation_is_required(piece, musician):
    part = SheetMusicPart(piece=piece, section="trubky", copyright_confirmed=False, file=pdf())
    with pytest.raises(CopyrightNotConfirmed):
        register_upload(part, actor=musician)
    with pytest.raises(ValidationError):
        part.clean()


def test_storage_name_is_generated_not_user_supplied(piece, musician):
    part = upload(piece, musician, name="../../etc/passwd.pdf")
    assert "passwd" not in part.file.name
    assert part.file.name.endswith(".pdf")
    assert part.sha256 and len(part.sha256) == 64
    assert part.size_bytes == len(MINIMAL_PDF)


def test_new_upload_creates_new_current_version(piece, musician):
    first = upload(piece, musician)
    second = upload(piece, musician)
    first.refresh_from_db()
    assert (first.version, first.is_current) == (1, False)
    assert (second.version, second.is_current) == (2, True)


def test_file_has_no_public_url(piece, musician):
    part = upload(piece, musician)
    with pytest.raises(ValueError, match="public URL"):
        part.file.url  # noqa: B018


def test_download_requires_login(client, piece, musician):
    part = upload(piece, musician)
    response = client.get(reverse("sheet_music:download", args=[part.pk]))
    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


def test_download_denied_without_portal_permission(login, make_user, piece, musician):
    part = upload(piece, musician)
    outsider = make_user([], profile=False)
    assert login(outsider).get(reverse("sheet_music:download", args=[part.pk])).status_code == 403


def test_musician_downloads_pdf_with_safe_headers(login, piece, musician):
    part = upload(piece, musician)
    response = login(musician).get(reverse("sheet_music:download", args=[part.pk]))
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    disposition = response["Content-Disposition"]
    assert disposition.startswith("attachment")
    assert "Skoda-lasky" in disposition
    assert "no-store" in response["Cache-Control"]
    assert b"".join(response.streaming_content).startswith(b"%PDF-")


def test_archived_piece_and_old_versions_are_not_downloadable(login, piece, musician):
    old = upload(piece, musician)
    current = upload(piece, musician)
    client = login(musician)
    assert client.get(reverse("sheet_music:download", args=[old.pk])).status_code == 404
    piece.is_archived = True
    piece.save()
    assert client.get(reverse("sheet_music:download", args=[current.pk])).status_code == 404


def test_listing_hides_archived_and_old_versions(login, piece, musician):
    upload(piece, musician)
    hidden = Piece.objects.create(title="Archivní skladba", is_archived=True)
    upload(hidden, musician)
    html = login(musician).get(reverse("sheet_music:list")).content.decode()
    assert "Škoda lásky" in html
    assert "Archivní skladba" not in html


def test_list_ignores_invalid_section_filter(login, musician):
    assert login(musician).get(reverse("sheet_music:list"), {"sekce": "<x>"}).status_code == 200


def test_download_logs_audit_event(login, piece, musician, caplog):
    part = upload(piece, musician)
    with caplog.at_level("INFO", logger="security"):
        login(musician).get(reverse("sheet_music:download", args=[part.pk]))
    assert any("sheet_music_downloaded" in r.getMessage() or "sheet_music_downloaded" in str(r.__dict__) for r in caplog.records)
