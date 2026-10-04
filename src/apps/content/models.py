from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class PageKey(models.TextChoices):
    HOME_HERO = "home-hero", "Úvod: hlavní text"
    HOME_INTRO = "home-intro", "Úvod: představení"
    ABOUT_HISTORY = "about-history", "O kapele: historie"
    ABOUT_STYLE = "about-style", "O kapele: hudební styl"
    ABOUT_CURRENT = "about-current", "O kapele: současná podoba"
    PRIVACY = "ochrana-osobnich-udaju", "Ochrana osobních údajů"
    COOKIES = "cookies", "Cookies"
    OPERATOR = "provozovatel", "Provozovatel webu"
    ACCESSIBILITY = "prohlaseni-o-pristupnosti", "Prohlášení o přístupnosti"
    SECURITY = "bezpecnost", "Bezpečnostní kontakt"
    PHOTO_REMOVAL = "odstraneni-fotografie", "Odstranění fotografie"


class Page(models.Model):
    """Editable plain-text page. Text is escaped on output; no HTML is stored or trusted."""

    key = models.CharField("klíč", max_length=40, choices=PageKey.choices, unique=True)
    title = models.CharField("nadpis", max_length=160)
    intro = models.TextField("úvod", blank=True)
    body = models.TextField("text", blank=True, help_text="Prostý text; odstavce oddělte prázdným řádkem.")
    needs_legal_review = models.BooleanField(
        "vyžaduje právní kontrolu",
        default=False,
        help_text="Zobrazí veřejné upozornění, že text není finální.",
    )
    updated_at = models.DateTimeField("upraveno", auto_now=True)

    class Meta:
        verbose_name = "stránka"
        verbose_name_plural = "stránky"
        ordering = ["key"]

    def __str__(self) -> str:
        return self.title


class SiteSettings(models.Model):
    """Singleton with public contact details and operator identity (placeholders by default)."""

    band_name = models.CharField("název kapely", max_length=120, default="Dechová hudba Oderské chasy")
    contact_email = models.EmailField("kontaktní e-mail", blank=True)
    contact_phone = models.CharField("kontaktní telefon", max_length=40, blank=True)
    contact_address = models.TextField("kontaktní adresa", blank=True)
    operator_name = models.CharField("provozovatel", max_length=200, blank=True)
    operator_details = models.TextField("údaje o provozovateli", blank=True)

    class Meta:
        verbose_name = "nastavení webu"
        verbose_name_plural = "nastavení webu"
        constraints = [
            models.CheckConstraint(
                condition=Q(pk=1),
                name="content_sitesettings_singleton",
                violation_error_message="Nastavení webu může existovat jen jednou.",
            )
        ]

    def save(self, *args: object, **kwargs: object) -> None:
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "SiteSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self) -> str:
        return "Nastavení webu"


class Announcement(models.Model):
    """Internal announcement shown to musicians in the portal."""

    title = models.CharField("nadpis", max_length=160)
    body = models.TextField("text")
    published_at = models.DateTimeField("zveřejněno od", default=timezone.now)
    expires_at = models.DateTimeField("platí do", null=True, blank=True)
    is_active = models.BooleanField("aktivní", default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="autor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        editable=False,
    )
    created_at = models.DateTimeField("vytvořeno", auto_now_add=True)

    class Meta:
        verbose_name = "interní oznámení"
        verbose_name_plural = "interní oznámení"
        ordering = ["-published_at"]
        indexes = [models.Index(fields=["is_active", "published_at"], name="content_ann_active_idx")]
        constraints = [
            models.CheckConstraint(
                condition=Q(expires_at__isnull=True) | Q(expires_at__gt=F("published_at")),
                name="content_announcement_expires_after_publish",
                violation_error_message="Konec platnosti musí být po začátku zveřejnění.",
            )
        ]

    def __str__(self) -> str:
        return self.title
