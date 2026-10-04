"""Tiny environment-variable helpers (no third-party dependency)."""

import os
from collections.abc import Sequence
from urllib.parse import parse_qs, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off", ""}


def get_str(name: str, default: str | None = None, *, required: bool = False) -> str | None:
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        if required:
            raise ImproperlyConfigured(f"Required environment variable {name} is not set.")
        return default
    return value.strip()


def require_str(name: str) -> str:
    value = get_str(name, required=True)
    assert value is not None  # noqa: S101 - narrowing for type checkers
    return value


def get_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in _TRUE:
        return True
    if value in _FALSE:
        return False
    raise ImproperlyConfigured(f"Environment variable {name} must be a boolean, got {raw!r}.")


def get_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ImproperlyConfigured(f"Environment variable {name} must be an integer.") from exc


def get_list(name: str, default: Sequence[str] = ()) -> list[str]:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return list(default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def parse_database_url(url: str) -> dict[str, object]:
    """Convert a postgresql:// or sqlite:// URL to a Django DATABASES entry."""
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme in {"postgres", "postgresql"}:
        options: dict[str, str] = {}
        for key, values in parse_qs(parsed.query).items():
            options[key] = values[-1]
        config: dict[str, object] = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": unquote(parsed.path.lstrip("/")),
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname or "",
            "PORT": str(parsed.port or ""),
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
        }
        if options:
            config["OPTIONS"] = options
        return config
    if scheme == "sqlite":
        path = unquote(parsed.path)
        # sqlite:///relative.db -> relative.db ; sqlite:////abs/path.db -> /abs/path.db
        name = path[1:] if path.startswith("/") else path
        return {"ENGINE": "django.db.backends.sqlite3", "NAME": name or ":memory:"}
    raise ImproperlyConfigured(f"Unsupported DATABASE_URL scheme {scheme!r}.")
