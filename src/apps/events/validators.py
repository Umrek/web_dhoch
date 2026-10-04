from urllib.parse import urlparse

from django.core.exceptions import ValidationError


def validate_https_url(value: str) -> None:
    """Only https links are accepted (prevents javascript:, data: and plain http)."""
    if urlparse(value).scheme.lower() != "https":
        raise ValidationError("Odkaz musí začínat https://.")
