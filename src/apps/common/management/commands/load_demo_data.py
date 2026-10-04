"""Idempotent, fictional demo data for LOCAL development only."""

import io
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ImproperlyConfigured
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from PIL import Image

from apps.accounts import roles
from apps.accounts.models import User
from apps.accounts.services import refresh_staff_flag
from apps.content.models import Announcement
from apps.events.models import Event, EventKind, EventStatus
from apps.gallery.images import process_image
from apps.gallery.models import Album, GalleryImage
from apps.gallery.services import store_image
from apps.musicians.models import MusicianProfile
from apps.sheet_music.models import Piece, SheetMusicPart
from apps.sheet_music.services import register_upload

MINIMAL_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF\n"
)

# (email, name, section, roles, public)  – all addresses use the reserved .invalid TLD
PEOPLE = [
    ("admin@demo.invalid", "Demo Administrátor", "kapelnik", [roles.ADMINISTRATOR], True),
    ("organizator@demo.invalid", "Demo Organizátor", "trubky", [roles.EVENT_ORGANIZER, roles.MUSICIAN], True),
    ("redaktor@demo.invalid", "Demo Redaktor", "klarinety", [roles.CONTENT_EDITOR], False),
    ("muzikant1@demo.invalid", "Demo Muzikant Jedna", "kridlovky", [roles.MUSICIAN], True),
    ("muzikant2@demo.invalid", "Demo Muzikant Dva", "basy", [roles.MUSICIAN], False),
]


def _demo_jpeg() -> SimpleUploadedFile:
    buffer = io.BytesIO()
    Image.new("RGB", (1200, 800), (122, 31, 43)).save(buffer, format="JPEG")
    return SimpleUploadedFile("demo.jpg", buffer.getvalue(), content_type="image/jpeg")


class Command(BaseCommand):
    help = "Create fictional demo accounts, events, gallery and sheet music (never in production)."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--password", help="Password for all demo accounts (default: random, printed once).")

    def handle(self, *args, **options) -> None:
        if not settings.DEBUG or settings.SETTINGS_MODULE.endswith("production"):
            raise CommandError("load_demo_data runs only with DEBUG=True and non-production settings.")
        try:
            call_command("sync_roles")
        except ImproperlyConfigured as exc:  # pragma: no cover
            raise CommandError(str(exc)) from exc

        password = options["password"] or secrets.token_urlsafe(16)
        created_any = False
        for email, name, section, role_names, public in PEOPLE:
            user, created = User.objects.get_or_create(email=email, defaults={"full_name": name})
            if created:
                user.set_password(password)
                user.save()
                created_any = True
            user.groups.set(Group.objects.filter(name__in=role_names))
            refresh_staff_flag(user)
            MusicianProfile.objects.get_or_create(
                user=user,
                defaults={"display_name": name, "section": section, "public_listing": public},
            )

        now = timezone.now()
        samples = [
            ("demo-koncert-v-parku", "Demo koncert v parku", EventKind.CONCERT, 21, True),
            ("demo-zkouska", "Demo pravidelná zkouška", EventKind.REHEARSAL, 3, False),
            ("demo-hodovy-pruvod", "Demo hodový průvod", EventKind.CONCERT, 45, True),
        ]
        for slug, title, kind, days, public in samples:
            start = (now + timedelta(days=days)).replace(hour=18, minute=0, second=0, microsecond=0)
            Event.objects.get_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "kind": kind,
                    "status": EventStatus.CONFIRMED,
                    "is_public": public,
                    "starts_at": start,
                    "meeting_time": start - timedelta(minutes=45),
                    "venue_name": "Demo místo",
                    "venue_address": "Ukázková 1, Odry",
                    "public_description": "Fiktivní ukázková akce.",
                    "internal_notes": "Oblečení: ukázkové. [Doplní organizátor]",
                },
            )

        Announcement.objects.get_or_create(title="Demo oznámení", defaults={"body": "Fiktivní interní oznámení."})

        album, _ = Album.objects.get_or_create(
            slug="demo-album", defaults={"title": "Demo album", "is_published": True}
        )
        if not album.images.exists():
            image = GalleryImage(album=album, alt_text="Ukázková jednobarevná fotografie", is_published=True)
            store_image(image, process_image(_demo_jpeg()), actor=None)

        piece, _ = Piece.objects.get_or_create(title="Demo polka", defaults={"composer": "Fiktivní skladatel"})
        if not piece.parts.exists():
            part = SheetMusicPart(
                piece=piece,
                section="trubky",
                copyright_confirmed=True,
                file=SimpleUploadedFile("demo.pdf", MINIMAL_PDF, content_type="application/pdf"),
            )
            register_upload(part, actor=None)

        self.stdout.write(self.style.SUCCESS("Demo data ready (fictional)."))
        if created_any:
            self.stdout.write(f"Demo accounts use the password: {password}")
            self.stdout.write("Accounts: " + ", ".join(p[0] for p in PEOPLE))
