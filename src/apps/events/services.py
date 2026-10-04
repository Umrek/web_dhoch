"""Event use cases. Multi-step state changes are atomic and logged."""

from datetime import datetime

from django.db import transaction
from django.utils import timezone

from apps.common.audit import log_admin_event

from .models import Event, EventKind, EventStatus


class EventServiceError(Exception):
    """Base class for expected, user-presentable event workflow errors."""


class InvalidStatusTransition(EventServiceError):
    pass


class EventAlreadyStarted(EventServiceError):
    pass


class EventNotPublishable(EventServiceError):
    pass


_ALLOWED: dict[str, set[str]] = {
    EventStatus.PLANNED: {EventStatus.CONFIRMED, EventStatus.CANCELLED},
    EventStatus.CONFIRMED: {EventStatus.PLANNED, EventStatus.CANCELLED},
    EventStatus.CANCELLED: {EventStatus.PLANNED},
}


@transaction.atomic
def change_status(event: Event, new_status: str, *, actor: object, now: datetime | None = None) -> Event:
    locked = Event.objects.select_for_update().get(pk=event.pk)
    if locked.status == new_status:
        return locked
    if new_status not in _ALLOWED[locked.status]:
        raise InvalidStatusTransition(f"{locked.status} -> {new_status}")
    if locked.starts_at <= (now or timezone.now()):
        raise EventAlreadyStarted(str(locked.pk))
    locked.status = new_status
    locked.save(update_fields=["status", "updated_at"])
    log_admin_event(
        "event_status_changed",
        event_id=str(locked.pk),
        status=new_status,
        actor_id=str(getattr(actor, "pk", "")),
    )
    return locked


@transaction.atomic
def set_public(event: Event, *, public: bool, actor: object) -> Event:
    locked = Event.objects.select_for_update().get(pk=event.pk)
    if public and locked.kind == EventKind.REHEARSAL:
        raise EventNotPublishable("Zkoušku nelze zveřejnit.")
    if locked.is_public != public:
        locked.is_public = public
        locked.save(update_fields=["is_public", "updated_at"])
        log_admin_event(
            "event_publication_changed",
            event_id=str(locked.pk),
            public=public,
            actor_id=str(getattr(actor, "pk", "")),
        )
    return locked
