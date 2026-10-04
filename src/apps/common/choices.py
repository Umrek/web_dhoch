"""Instrument sections shared by musician profiles and sheet-music parts."""

from django.db import models


class InstrumentSection(models.TextChoices):
    CONDUCTOR = "kapelnik", "Kapelník"
    FLUGELHORN = "kridlovky", "Křídlovky"
    TRUMPET = "trubky", "Trubky"
    CLARINET = "klarinety", "Klarinety"
    TENOR_HORN = "tenory", "Tenory"
    BARITONE = "barytony", "Barytony"
    TROMBONE = "pozouny", "Pozouny"
    BASS = "basy", "Basy"
    PERCUSSION = "bici", "Bicí"
    VOCAL = "zpev", "Zpěv"
    SCORE = "partitura", "Partitura (všechny hlasy)"


def person_sections() -> list[tuple[str, str]]:
    """Sections a musician can belong to (the score is not a person's section)."""
    return [(v, label) for v, label in InstrumentSection.choices if v != InstrumentSection.SCORE]
