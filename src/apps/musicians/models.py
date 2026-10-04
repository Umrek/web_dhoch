from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

from apps.common.choices import person_sections

phone_validator = RegexValidator(
    r"^\+?[0-9 ]{9,16}$", "Zadejte telefon ve tvaru 123 456 789 nebo +420 123 456 789."
)


class MusicianProfile(models.Model):
    """Member profile. Public listing is opt-in (GDPR): only name, section and instrument.

    The phone number is never shown publicly and never listed on the public roster.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="musician_profile",
        verbose_name="uživatel",
    )
    display_name = models.CharField("jméno", max_length=120)
    section = models.CharField("sekce", max_length=12, choices=person_sections())
    instrument = models.CharField("nástroj", max_length=80, blank=True)
    public_listing = models.BooleanField(
        "zobrazit na veřejné stránce kapely",
        default=False,
        help_text="Zobrazí se pouze jméno, sekce a nástroj. Souhlas lze kdykoli odvolat.",
    )
    public_listing_changed_at = models.DateTimeField(
        "změna souhlasu se zveřejněním", null=True, blank=True, editable=False
    )
    phone = models.CharField(
        "telefon", max_length=20, blank=True, validators=[phone_validator],
        help_text="Viditelný jen správcům. Nepovinné.",
    )
    is_active_member = models.BooleanField("aktivní člen", default=True)
    created_at = models.DateTimeField("vytvořeno", auto_now_add=True)
    updated_at = models.DateTimeField("upraveno", auto_now=True)

    class Meta:
        verbose_name = "profil muzikanta"
        verbose_name_plural = "profily muzikantů"
        ordering = ["section", "display_name"]
        indexes = [
            models.Index(fields=["public_listing", "is_active_member"], name="musicians_public_idx")
        ]

    def __str__(self) -> str:
        return self.display_name
