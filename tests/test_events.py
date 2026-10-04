"""Public events, ICS export, and publication rules."""

from datetime import timedelta

import pytest
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from apps.events import selectors, services
from apps.events.ics import build_event_ics, escape_text, fold_line
from apps.events.validators import validate_https_url

pytestmark = pytest.mark.django_db


def test_public_list_hides_internal_and_past_events(client, make_event):
    make_event(title="Veřejný koncert")
    make_event(title="Interní akce", is_public=False)
    make_event(title="Dávno pryč", starts_at=timezone.now() - timedelta(days=3))
    html = client.get(reverse("events:list")).content.decode()
    assert "Veřejný koncert" in html
    assert "Interní akce" not in html
    assert "Dávno pryč" not in html


def test_public_pages_never_show_internal_notes(client, make_event):
    event = make_event()
    for url in (
        reverse("events:list"),
        reverse("events:detail", args=[event.slug]),
        reverse("content:home"),
        reverse("events:ics", args=[event.slug]),
    ):
        assert b"TAJNE-INTERNI-POKYNY" not in client.get(url).content


def test_non_public_event_detail_is_404(client, make_event):
    event = make_event(is_public=False)
    assert client.get(reverse("events:detail", args=[event.slug])).status_code == 404
    assert client.get(reverse("events:ics", args=[event.slug])).status_code == 404


def test_rehearsal_cannot_be_public(make_event):
    with pytest.raises(IntegrityError), transaction.atomic():
        make_event(kind="zkouska", is_public=True)


def test_rehearsal_constraint_enforced_by_database_on_update(make_event):
    # Bypasses model validation and services: only the DB CHECK constraint can stop this.
    from apps.events.models import Event

    rehearsal = make_event(kind="zkouska", is_public=False)
    with pytest.raises(IntegrityError), transaction.atomic():
        Event.objects.filter(pk=rehearsal.pk).update(is_public=True)
    rehearsal.refresh_from_db()
    assert rehearsal.is_public is False


@pytest.mark.parametrize(
    ("kind", "is_public"),
    [("zkouska", False), ("koncert", True), ("koncert", False), ("jina", True), ("jina", False)],
)
def test_allowed_kind_and_visibility_combinations(make_event, kind, is_public):
    event = make_event(kind=kind, is_public=is_public)
    event.full_clean()
    assert event.pk is not None


def test_set_public_service_rejects_rehearsal(make_event, organizer):
    rehearsal = make_event(kind="zkouska", is_public=False)
    with pytest.raises(services.EventNotPublishable):
        services.set_public(rehearsal, public=True, actor=organizer)


def test_end_must_follow_start(make_event):
    start = timezone.now() + timedelta(days=2)
    with pytest.raises(IntegrityError), transaction.atomic():
        make_event(starts_at=start, ends_at=start - timedelta(hours=1))


def test_cancelled_event_stays_visible_and_marked(client, make_event):
    event = make_event(status="zruseno")
    html = client.get(reverse("events:detail", args=[event.slug])).content.decode()
    assert "zrušena" in html.lower()


def test_status_change_rules(make_event, organizer):
    event = make_event(status="planovano")
    assert services.change_status(event, "potvrzeno", actor=organizer).status == "potvrzeno"
    past = make_event(starts_at=timezone.now() - timedelta(days=1), status="planovano")
    with pytest.raises(services.EventAlreadyStarted):
        services.change_status(past, "zruseno", actor=organizer)


def test_ics_download_content(client, make_event):
    event = make_event(title="Koncert; s čárkou, a středníkem", venue_name="Park")
    response = client.get(reverse("events:ics", args=[event.slug]))
    assert response["Content-Type"].startswith("text/calendar")
    assert "attachment" in response["Content-Disposition"]
    body = response.content.decode()
    assert body.startswith("BEGIN:VCALENDAR\r\n")
    assert "SUMMARY:Koncert\\; s čárkou\\, a středníkem" in body


def test_ics_lines_are_folded_and_header_injection_is_blocked(make_event):
    event = make_event(public_description="x" * 300 + "\r\nEND:VEVENT\r\nBEGIN:EVIL")
    body = build_event_ics(event)
    for line in body.split("\r\n"):
        assert len(line.encode()) <= 75
    assert "\r\nEND:VEVENT\r\nBEGIN:EVIL" not in body
    assert body.split("\r\n").count("END:VEVENT") == 1
    assert "BEGIN:EVIL" not in body.split("\r\n")


def test_escape_and_fold_helpers():
    assert escape_text("a,b;c\\d\ne") == "a\\,b\\;c\\\\d\\ne"
    assert escape_text("a\x00b") == "ab"
    assert fold_line("ě" * 100).split("\r\n ")[0].encode().__len__() <= 75


def test_map_url_must_be_https():
    from django.core.exceptions import ValidationError

    with pytest.raises(ValidationError):
        validate_https_url("javascript:alert(1)")
    with pytest.raises(ValidationError):
        validate_https_url("http://example.test")
    validate_https_url("https://example.test/mapa")


def test_month_grouping(make_event):
    make_event(starts_at=timezone.now() + timedelta(days=5))
    make_event(starts_at=timezone.now() + timedelta(days=65))
    groups = selectors.month_groups(selectors.upcoming_public())
    assert len(groups) == 2


def test_archive_pagination(client, make_event):
    for i in range(25):
        make_event(starts_at=timezone.now() - timedelta(days=i + 1))
    response = client.get(reverse("events:archive"))
    assert response.status_code == 200
    assert len(response.context["page"].object_list) == 20
