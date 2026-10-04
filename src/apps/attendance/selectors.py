from collections import Counter
from dataclasses import dataclass

from django.contrib.auth import get_user_model

from apps.common.choices import InstrumentSection
from apps.events.models import Event
from apps.musicians.models import MusicianProfile

from .models import AttendanceResponse, AttendanceStatus


def own_responses(user, events) -> dict[str, AttendanceResponse]:
    """Map event pk (str) -> the user's own response. Filters by user: no cross-user leakage."""
    rows = AttendanceResponse.objects.filter(user=user, event__in=list(events))
    return {str(r.event_id): r for r in rows}


@dataclass
class OverviewRow:
    name: str
    section: str
    status: str
    note: str


@dataclass
class Overview:
    rows: list[OverviewRow]
    counts: dict[str, int]
    missing: list[str]


def event_overview(event: Event) -> Overview:
    """Organizer view: answers, counts and active musicians who have not answered."""
    labels = dict(InstrumentSection.choices)
    status_labels = dict(AttendanceStatus.choices)
    profiles = {
        p.user_id: p
        for p in MusicianProfile.objects.filter(is_active_member=True, user__is_active=True)
    }
    responses = AttendanceResponse.objects.filter(event=event).select_related("user")
    rows: list[OverviewRow] = []
    answered: set = set()
    for response in responses:
        profile = profiles.get(response.user_id)
        answered.add(response.user_id)
        rows.append(
            OverviewRow(
                name=profile.display_name if profile else str(response.user),
                section=labels.get(profile.section, "") if profile else "",
                status=status_labels[response.status],
                note=response.note,
            )
        )
    rows.sort(key=lambda r: (r.section, r.name.casefold()))
    counter = Counter(r.status for r in responses)
    counts = {key: counter.get(key, 0) for key in AttendanceStatus.values}
    missing = sorted(
        (p.display_name for uid, p in profiles.items() if uid not in answered), key=str.casefold
    )
    return Overview(rows=rows, counts=counts, missing=missing)


def active_user_count() -> int:
    return get_user_model().objects.filter(is_active=True, musician_profile__isnull=False).count()
