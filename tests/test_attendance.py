"""Attendance: own-response-only writes, deadlines, organizer overview, concurrency invariants."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.attendance import services
from apps.attendance.models import AttendanceResponse
from apps.attendance.selectors import event_overview

pytestmark = pytest.mark.django_db


def test_musician_can_respond_and_change_answer(login, musician, make_event):
    event = make_event()
    client = login(musician)
    url = reverse("attendance:detail", args=[event.slug])
    assert client.post(url, {"status": "ano", "note": ""}).status_code == 302
    assert client.post(url, {"status": "ne", "note": "Nemoc"}).status_code == 302
    rows = AttendanceResponse.objects.filter(event=event, user=musician)
    assert rows.count() == 1
    assert rows.get().status == "ne"
    assert rows.get().note == "Nemoc"


def test_response_is_always_bound_to_session_user(login, musician, make_user, make_event):
    other = make_user()
    event = make_event()
    login(musician).post(
        reverse("attendance:detail", args=[event.slug]),
        {"status": "ano", "note": "", "user": other.pk, "user_id": other.pk},
    )
    assert AttendanceResponse.objects.filter(user=other).count() == 0
    assert AttendanceResponse.objects.filter(user=musician).count() == 1


def test_invalid_status_rejected(login, musician, make_event):
    event = make_event()
    response = login(musician).post(
        reverse("attendance:detail", args=[event.slug]), {"status": "hacker"}
    )
    assert response.status_code == 400
    assert AttendanceResponse.objects.count() == 0


def test_cannot_respond_after_deadline(musician, make_event):
    event = make_event(
        attendance_deadline=timezone.now() - timedelta(hours=1),
        starts_at=timezone.now() + timedelta(days=1),
    )
    with pytest.raises(services.ResponsesClosed):
        services.respond_to_event(user=musician, event=event, status="ano")


def test_cannot_respond_to_cancelled_or_started_or_disabled(musician, make_event):
    cancelled = make_event(status="zruseno")
    started = make_event(starts_at=timezone.now() - timedelta(minutes=5))
    disabled = make_event(attendance_enabled=False)
    for event in (cancelled, started, disabled):
        with pytest.raises(services.ResponsesClosed):
            services.respond_to_event(user=musician, event=event, status="ano")


def test_service_is_idempotent_for_same_answer(musician, make_event):
    event = make_event()
    services.respond_to_event(user=musician, event=event, status="ano")
    services.respond_to_event(user=musician, event=event, status="ano")
    assert AttendanceResponse.objects.filter(event=event, user=musician).count() == 1


def test_note_is_truncated_and_html_is_escaped_on_output(login, musician, organizer, make_event):
    event = make_event()
    services.respond_to_event(user=musician, event=event, status="ano", note="<script>x</script>" + "a" * 400)
    assert len(AttendanceResponse.objects.get().note) == 300
    html = login(organizer).get(reverse("attendance:overview", args=[event.slug])).content.decode()
    assert "<script>x" not in html


def test_overview_denied_for_musician_allowed_for_organizer(login, musician, organizer, make_event):
    event = make_event()
    url = reverse("attendance:overview", args=[event.slug])
    assert login(musician).get(url).status_code == 403
    assert login(organizer).get(url).status_code == 200


def test_overview_lists_missing_responders(musician, organizer, make_event):
    event = make_event()
    services.respond_to_event(user=musician, event=event, status="ano")
    overview = event_overview(event)
    assert overview.counts["ano"] == 1
    assert any(name.startswith("Muzikant") for name in overview.missing)  # the organizer has not answered


def test_member_list_shows_only_own_response(login, musician, make_user, make_event):
    other = make_user([*musician.groups.values_list("name", flat=True)])
    event = make_event()
    services.respond_to_event(user=other, event=event, status="ne", note="TAJNA-POZNAMKA-JINEHO")
    html = login(musician).get(reverse("attendance:list")).content.decode()
    assert "TAJNA-POZNAMKA-JINEHO" not in html


def test_member_pages_show_internal_notes_to_members_only(client, login, musician, make_event):
    event = make_event()
    url = reverse("attendance:detail", args=[event.slug])
    assert client.get(url).status_code == 302
    assert "TAJNE-INTERNI-POKYNY" in login(musician).get(url).content.decode()
