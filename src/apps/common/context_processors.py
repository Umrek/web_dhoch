from django.conf import settings
from django.http import HttpRequest


def site(request: HttpRequest) -> dict[str, object]:
    return {
        "SITE_NAME": settings.SITE_NAME,
        "PRIVACY_CONTACT_EMAIL": settings.PRIVACY_CONTACT_EMAIL,
        "SECURITY_CONTACT_EMAIL": settings.SECURITY_CONTACT_EMAIL,
        "CONTACT_RETENTION_DAYS": settings.CONTACT_RETENTION_DAYS,
    }
