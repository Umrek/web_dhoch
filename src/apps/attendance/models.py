from django.conf import settings
from django.db import models

from apps.events.models import Event


class AttendanceStatus(models.TextChoices):
    YES = "ano", "Přijdu"
    NO = "ne", "Nepřijdu"
    MAYBE = "mozna", "Zatím nevím"


class AttendanceResponse(models.Model):
    """One musician's answer for one event. Exactly one row per (event, user)."""

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="attendance_responses", verbose_name="akce"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attendance_responses",
        verbose_name="muzikant",
    )
    status = models.CharField("odpověď", max_length=6, choices=AttendanceStatus.choices)
    note = models.CharField("poznámka", max_length=300, blank=True)
    responded_at = models.DateTimeField("poprvé odpovězeno", auto_now_add=True)
    updated_at = models.DateTimeField("naposledy změněno", auto_now=True)

    class Meta:
        verbose_name = "odpověď o docházce"
        verbose_name_plural = "odpovědi o docházce"
        ordering = ["event__starts_at", "user__email"]
        constraints = [
            models.UniqueConstraint(fields=["event", "user"], name="attendance_unique_event_user")
        ]
        indexes = [models.Index(fields=["event", "status"], name="attendance_event_status_idx")]

    def __str__(self) -> str:
        return f"{self.user_id} → {self.event_id}: {self.status}"
