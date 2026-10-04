"""Minimal, safe iCalendar (RFC 5545) generation for a single public event."""

import re
from datetime import UTC, datetime

from django.conf import settings
from django.utils import timezone

from .models import Event, EventStatus

_STATUS = {
    EventStatus.PLANNED: "TENTATIVE",
    EventStatus.CONFIRMED: "CONFIRMED",
    EventStatus.CANCELLED: "CANCELLED",
}
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def escape_text(value: str) -> str:
    value = _CONTROL.sub("", value)
    value = value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
    return value.replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n")


def fold_line(line: str) -> str:
    """Fold at 75 octets without splitting UTF-8 sequences."""
    if len(line.encode("utf-8")) <= 75:
        return line
    parts: list[str] = []
    current = ""
    limit = 75
    for char in line:
        if len((current + char).encode("utf-8")) > limit:
            parts.append(current)
            current = char
            limit = 74  # continuation lines start with one space
        else:
            current += char
    parts.append(current)
    return "\r\n ".join(parts)


def _utc(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def build_event_ics(event: Event, *, now: datetime | None = None) -> str:
    host = settings.SITE_URL.split("://", 1)[-1] or "localhost"
    location = ", ".join(p for p in (event.venue_name, event.venue_address) if p)
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Dechova hudba Oderske chasy//Web//CS",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{event.id}@{host}",
        f"DTSTAMP:{_utc(now or timezone.now())}",
        f"DTSTART:{_utc(event.starts_at)}",
        f"DTEND:{_utc(event.effective_end)}",
        f"SUMMARY:{escape_text(event.title)}",
        f"STATUS:{_STATUS[event.status]}",
    ]
    if location:
        lines.append(f"LOCATION:{escape_text(location)}")
    if event.public_description:  # never the internal notes
        lines.append(f"DESCRIPTION:{escape_text(event.public_description)}")
    lines.append(f"URL:{settings.SITE_URL}{event.get_absolute_url()}")
    lines += ["END:VEVENT", "END:VCALENDAR"]
    return "\r\n".join(fold_line(line) for line in lines) + "\r\n"
