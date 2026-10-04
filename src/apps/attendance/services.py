"""Attendance use cases. The responding user is always taken from the session, never from input."""

from datetime import datetime

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.common.audit import log_security_event
from apps.events.models import Event

from .models import AttendanceResponse, AttendanceStatus


class AttendanceError(Exception):
    pass


class ResponsesClosed(AttendanceError):
    """Event cancelled, started, attendance disabled, or deadline passed."""


class InvalidStatus(AttendanceError):
    pass


@transaction.atomic
def respond_to_event(
    *, user, event: Event, status: str, note: str = "", now: datetime | None = None
) -> AttendanceResponse:
    """Create or update the user's own response, atomically and idempotently."""
    if status not in AttendanceStatus.values:
        raise InvalidStatus(status)
    locked = Event.objects.select_for_update().get(pk=event.pk)
    if not locked.accepts_responses(now or timezone.now()):
        raise ResponsesClosed(str(locked.pk))
    note = note.strip()[:300]
    values = {"status": status, "note": note}
    try:
        with transaction.atomic():
            response, created = AttendanceResponse.objects.update_or_create(
                event=locked, user=user, defaults=values
            )
    except IntegrityError:  # concurrent first insert: fall back to update
        response = AttendanceResponse.objects.get(event=locked, user=user)
        response.status, response.note = status, note
        response.save(update_fields=["status", "note", "updated_at"])
        created = False
    log_security_event(
        "attendance_recorded",
        user_id=str(user.pk),
        event_id=str(locked.pk),
        status=status,
        created=created,
    )
    return response
