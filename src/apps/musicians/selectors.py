from itertools import groupby

from apps.common.choices import InstrumentSection

from .models import MusicianProfile

_ORDER = [value for value, _ in InstrumentSection.choices]


def public_roster() -> list[tuple[str, list[MusicianProfile]]]:
    """Opted-in, active members with active accounts, grouped by section.

    Only fields intended for public display are loaded (no phone, no e-mail).
    """
    profiles = list(
        MusicianProfile.objects.filter(
            public_listing=True, is_active_member=True, user__is_active=True
        ).only("id", "display_name", "section", "instrument")
    )
    profiles.sort(key=lambda p: (_ORDER.index(p.section), p.display_name.casefold()))
    labels = dict(InstrumentSection.choices)
    return [
        (labels[section], list(items)) for section, items in groupby(profiles, key=lambda p: p.section)
    ]


def profile_for(user) -> MusicianProfile | None:
    return MusicianProfile.objects.filter(user=user).first()
