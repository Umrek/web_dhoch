"""Shared fixtures. All data is fictional; e-mail addresses use the reserved example.test domain."""

import io
import itertools
from datetime import timedelta

import pytest
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.utils import timezone
from PIL import Image

from apps.accounts import roles
from apps.accounts.models import User
from apps.accounts.services import refresh_staff_flag
from apps.events.models import Event
from apps.musicians.models import MusicianProfile

PASSWORD = "Spravne-Koleno-Baterie-2026"  # noqa: S105 - test-only value

MINIMAL_PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()


@pytest.fixture
def make_user(db):
    roles.sync_roles()
    counter = itertools.count(1)

    def factory(
        role_names=(),
        *,
        email=None,
        section="trubky",
        profile=True,
        public=False,
        phone="",
        active=True,
    ) -> User:
        n = next(counter)
        user = User.objects.create_user(
            email=email or f"user{n}@example.test",
            password=PASSWORD,
            full_name=f"Testovací Uživatel {n}",
            is_active=active,
        )
        user.groups.set(Group.objects.filter(name__in=role_names))
        refresh_staff_flag(user)
        if profile:
            MusicianProfile.objects.create(
                user=user,
                display_name=f"Muzikant {n}",
                section=section,
                public_listing=public,
                phone=phone,
            )
        return user

    return factory


@pytest.fixture
def musician(make_user):
    return make_user([roles.MUSICIAN])


@pytest.fixture
def organizer(make_user):
    return make_user([roles.EVENT_ORGANIZER, roles.MUSICIAN])


@pytest.fixture
def editor(make_user):
    return make_user([roles.CONTENT_EDITOR])


@pytest.fixture
def admin_user(make_user):
    return make_user([roles.ADMINISTRATOR])


@pytest.fixture
def make_event(db):
    counter = itertools.count(1)

    def factory(**overrides) -> Event:
        n = next(counter)
        values = {
            "title": f"Koncert {n}",
            "slug": f"koncert-{n}",
            "kind": "koncert",
            "status": "potvrzeno",
            "is_public": True,
            "starts_at": timezone.now() + timedelta(days=7),
            "internal_notes": "TAJNE-INTERNI-POKYNY",
            "public_description": "Veřejný popis",
        }
        values.update(overrides)
        return Event.objects.create(**values)

    return factory


@pytest.fixture
def login(client):
    def do_login(user: User):
        client.force_login(user)
        return client

    return do_login


def make_image_bytes(size=(64, 32), fmt="JPEG", **save_kwargs) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, (10, 120, 60)).save(buffer, format=fmt, **save_kwargs)
    return buffer.getvalue()
