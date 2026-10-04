"""Public pages, privacy defaults, SEO files and health endpoints."""

import pytest
from django.urls import reverse

from apps.content.models import Page, PageKey
from apps.content.views import LEGAL_SLUGS

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("name", ["content:home", "content:about", "events:list", "gallery:list", "contact:form"])
def test_public_pages_render_in_czech(client, name):
    response = client.get(reverse(name))
    assert response.status_code == 200
    assert '<html lang="cs">' in response.content.decode()


@pytest.mark.parametrize("slug", sorted(LEGAL_SLUGS))
def test_legal_pages_render_with_review_notice(client, slug):
    response = client.get(reverse("content:legal", args=[slug]))
    assert response.status_code == 200
    assert "právně zkontrolován" in response.content.decode()


def test_unknown_legal_slug_is_404(client):
    assert client.get("/pravni/neexistuje/").status_code == 404


def test_page_text_is_escaped_not_trusted(client):
    Page.objects.create(key=PageKey.ABOUT_HISTORY, title="Historie", body="<script>alert(1)</script>")
    html = client.get(reverse("content:about")).content.decode()
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_roster_lists_only_opted_in_active_members_without_private_data(client, make_user):
    public = make_user(["Muzikant"], public=True, phone="777 123 456", email="verejny@example.test")
    make_user(["Muzikant"], public=False, phone="777 000 111", email="soukromy@example.test")
    inactive = make_user(["Muzikant"], public=True, active=False)
    html = client.get(reverse("content:about")).content.decode()
    assert public.musician_profile.display_name in html
    assert inactive.musician_profile.display_name not in html
    for secret in ("777 123 456", "777 000 111", "verejny@example.test", "soukromy@example.test"):
        assert secret not in html


def test_withdrawing_consent_removes_member_from_public_page(login, client, make_user):
    user = make_user(["Muzikant"], public=True)
    name = user.musician_profile.display_name
    assert name in client.get(reverse("content:about")).content.decode()
    login(user).post(
        reverse("musicians:profile"),
        {"display_name": name, "instrument": "", "phone": ""},
    )
    user.musician_profile.refresh_from_db()
    assert user.musician_profile.public_listing is False
    assert user.musician_profile.public_listing_changed_at is not None
    assert name not in client.get(reverse("content:about")).content.decode()


def test_profile_view_only_edits_own_profile(login, make_user):
    me = make_user(["Muzikant"])
    other = make_user(["Muzikant"])
    login(me).post(
        reverse("musicians:profile"),
        {"display_name": "Nové jméno", "instrument": "", "phone": "", "section": "bici", "user": other.pk},
    )
    me.musician_profile.refresh_from_db()
    other.musician_profile.refresh_from_db()
    assert me.musician_profile.display_name == "Nové jméno"
    assert me.musician_profile.section == "trubky"  # section is not self-editable
    assert other.musician_profile.display_name != "Nové jméno"


def test_invalid_phone_rejected(login, musician):
    response = login(musician).post(
        reverse("musicians:profile"),
        {"display_name": "X", "instrument": "", "phone": "<script>"},
    )
    assert response.status_code == 400


def test_robots_and_security_txt(client):
    robots = client.get("/robots.txt")
    assert robots["Content-Type"].startswith("text/plain")
    assert "Disallow: /portal/" in robots.content.decode()
    sec = client.get("/.well-known/security.txt")
    assert sec["Content-Type"].startswith("text/plain")
    assert "Contact: mailto:" in sec.content.decode()
    assert "Expires:" in sec.content.decode()


def test_health_endpoints_expose_nothing_internal(client):
    for name in ("live", "ready"):
        response = client.get(reverse(f"common:{name}"))
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert "no-cache" in response["Cache-Control"] or "no-store" in response["Cache-Control"]


def test_dashboard_shows_announcements_to_members_only(client, login, musician):
    from apps.content.models import Announcement

    Announcement.objects.create(title="Interní zpráva", body="Jen pro členy")
    assert "Interní zpráva" not in client.get(reverse("content:home")).content.decode()
    assert "Interní zpráva" in login(musician).get(reverse("musicians:dashboard")).content.decode()


def test_expired_announcements_are_hidden(login, musician):
    from datetime import timedelta

    from django.utils import timezone

    from apps.content.models import Announcement

    now = timezone.now()
    Announcement.objects.create(
        title="Prošlé oznámení", body="x", published_at=now - timedelta(days=5), expires_at=now - timedelta(days=1)
    )
    assert "Prošlé oznámení" not in login(musician).get(reverse("musicians:dashboard")).content.decode()


def test_portal_pages_are_noindex(login, musician):
    html = login(musician).get(reverse("musicians:dashboard")).content.decode()
    assert 'name="robots" content="noindex, nofollow"' in html
