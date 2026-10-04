import uuid
from datetime import datetime, timedelta
from urllib.parse import quote

from django.db import models
from django.db.models import F, Q
from django.urls import reverse

from .validators import validate_https_url


class EventKind(models.TextChoices):
    CONCERT = "koncert", "Koncert"
    REHEARSAL = "zkouska", "Zkouška"
    OTHER = "jina", "Jiná akce"


class EventStatus(models.TextChoices):
    PLANNED = "planovano", "Plánováno"
    CONFIRMED = "potvrzeno", "Potvrzeno"
    CANCELLED = "zruseno", "Zrušeno"


class Event(models.Model):
    """Concert, rehearsal or other event.

    ``is_public`` controls publication on the public website. Rehearsals can never be
    public (database constraint). ``internal_notes`` are visible to musicians only.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField("název", max_length=160)
    slug = models.SlugField("adresa (slug)", max_length=100, unique=True)
    kind = models.CharField("druh", max_length=10, choices=EventKind.choices, default=EventKind.CONCERT)
    status = models.CharField(
        "stav", max_length=10, choices=EventStatus.choices, default=EventStatus.PLANNED
    )
    is_public = models.BooleanField(
        "zveřejnit na webu", default=False, help_text="Zkoušky nelze zveřejnit."
    )
    starts_at = models.DateTimeField("začátek vystoupení / akce")
    ends_at = models.DateTimeField("konec", null=True, blank=True)
    meeting_time = models.DateTimeField("sraz", null=True, blank=True)
    venue_name = models.CharField("místo", max_length=160, blank=True)
    venue_address = models.CharField("adresa místa", max_length=250, blank=True)
    map_url = models.URLField(
        "odkaz na mapu",
        blank=True,
        validators=[validate_https_url],
        help_text="Volitelné; jinak se vytvoří odkaz na OpenStreetMap z adresy.",
    )
    public_description = models.TextField("veřejný popis", blank=True)
    internal_notes = models.TextField(
        "interní pokyny pro muzikanty",
        blank=True,
        help_text="Nikdy se nezobrazují veřejně (oblečení, doprava, repertoár...).",
    )
    attendance_enabled = models.BooleanField("sbírat docházku", default=True)
    attendance_deadline = models.DateTimeField("uzávěrka odpovědí", null=True, blank=True)
    created_at = models.DateTimeField("vytvořeno", auto_now_add=True)
    updated_at = models.DateTimeField("upraveno", auto_now=True)

    class Meta:
        verbose_name = "akce"
        verbose_name_plural = "akce"
        ordering = ["starts_at"]
        indexes = [
            models.Index(fields=["starts_at"], name="events_event_starts_idx"),
            models.Index(fields=["is_public", "starts_at"], name="events_event_public_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(ends_at__isnull=True) | Q(ends_at__gt=F("starts_at")),
                name="events_event_ends_after_start",
                violation_error_message="Konec musí být po začátku.",
            ),
            models.CheckConstraint(
                condition=Q(meeting_time__isnull=True) | Q(meeting_time__lte=F("starts_at")),
                name="events_event_meeting_before_start",
                violation_error_message="Sraz nemůže být po začátku.",
            ),
            models.CheckConstraint(
                condition=Q(attendance_deadline__isnull=True)
                | Q(attendance_deadline__lte=F("starts_at")),
                name="events_event_deadline_before_start",
                violation_error_message="Uzávěrka nemůže být po začátku.",
            ),
            models.CheckConstraint(
                condition=~Q(kind="zkouska", is_public=True),
                name="events_event_rehearsal_not_public",
                violation_error_message="Zkoušku nelze zveřejnit na veřejném webu.",
            ),
        ]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("events:detail", kwargs={"slug": self.slug})

    @property
    def is_cancelled(self) -> bool:
        return self.status == EventStatus.CANCELLED

    @property
    def effective_end(self) -> datetime:
        return self.ends_at or self.starts_at + timedelta(hours=2)

    def accepts_responses(self, now: datetime) -> bool:
        """Can musicians still answer? (enabled, not cancelled, not started, before deadline)"""
        if not self.attendance_enabled or self.is_cancelled or self.starts_at <= now:
            return False
        return self.attendance_deadline is None or now <= self.attendance_deadline

    @property
    def map_link(self) -> str:
        if self.map_url:
            return self.map_url
        query = " ".join(part for part in (self.venue_name, self.venue_address) if part).strip()
        if not query:
            return ""
        return f"https://www.openstreetmap.org/search?query={quote(query)}"
