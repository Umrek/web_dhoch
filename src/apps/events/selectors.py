"""Read operations for events (public site and member portal)."""

from collections.abc import Iterable
from datetime import date, datetime
from itertools import groupby

from django.db.models import QuerySet
from django.utils import timezone

from .models import Event, EventKind


def _now(now: datetime | None) -> datetime:
    return now or timezone.now()


def upcoming_public(*, limit: int | None = None, now: datetime | None = None) -> list[Event]:
    queryset = Event.objects.filter(is_public=True, starts_at__gte=_now(now)).order_by("starts_at")
    return list(queryset[:limit] if limit else queryset)


def past_public(*, now: datetime | None = None) -> QuerySet[Event]:
    return Event.objects.filter(is_public=True, starts_at__lt=_now(now)).order_by("-starts_at")


def public_event(slug: str) -> Event | None:
    return Event.objects.filter(slug=slug, is_public=True).first()


def month_groups(events: Iterable[Event]) -> list[tuple[date, list[Event]]]:
    """Group events by calendar month in the local time zone."""

    def key(event: Event) -> tuple[int, int]:
        local = timezone.localtime(event.starts_at)
        return local.year, local.month

    return [
        (date(year, month, 1), list(items))
        for (year, month), items in groupby(sorted(events, key=lambda e: e.starts_at), key=key)
    ]


def member_events(
    *, now: datetime | None = None, kind: str | None = None, upcoming: bool = True
) -> QuerySet[Event]:
    """Events visible to musicians (includes rehearsals and non-public events)."""
    queryset = Event.objects.all()
    if kind:
        queryset = queryset.filter(kind=kind)
    if upcoming:
        return queryset.filter(starts_at__gte=_now(now)).order_by("starts_at")
    return queryset.filter(starts_at__lt=_now(now)).order_by("-starts_at")


def next_rehearsals(limit: int = 3, now: datetime | None = None) -> list[Event]:
    return list(member_events(now=now, kind=EventKind.REHEARSAL)[:limit])


def next_concerts(limit: int = 3, now: datetime | None = None) -> list[Event]:
    return list(member_events(now=now, kind=EventKind.CONCERT)[:limit])
