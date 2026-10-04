from django.db import models


class ContactMessage(models.Model):
    """Stored inquiry. Personal data: kept only for ``CONTACT_RETENTION_DAYS``, no IP stored."""

    name = models.CharField("jméno", max_length=120)
    email = models.EmailField("e-mail", max_length=254)
    message = models.TextField("zpráva", max_length=4000)
    consent_given_at = models.DateTimeField("souhlas se zpracováním", auto_now_add=True)
    email_sent = models.BooleanField("e-mail odeslán", default=False)
    is_handled = models.BooleanField("vyřízeno", default=False)
    created_at = models.DateTimeField("přijato", auto_now_add=True)

    class Meta:
        verbose_name = "zpráva z kontaktního formuláře"
        verbose_name_plural = "zprávy z kontaktního formuláře"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["created_at"], name="contact_created_idx")]

    def __str__(self) -> str:
        return f"{self.name} ({self.created_at:%d. %m. %Y})"
