"""Automated-test settings: fast, isolated, no external services."""

import tempfile
from pathlib import Path

from .base import *  # noqa: F403
from .env import get_str, parse_database_url

DEBUG = False
SECRET_KEY = "test-only-secret-key-not-used-anywhere-else"  # noqa: S105
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
# CI sets DATABASE_URL to a throwaway PostgreSQL service so tests also run on the production engine.
if _test_db_url := get_str("DATABASE_URL", ""):
    DATABASES = {"default": parse_database_url(_test_db_url)}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Axes is exercised explicitly in dedicated tests via override_settings.
AXES_ENABLED = False

_TMP = Path(tempfile.mkdtemp(prefix="oderske-chasy-tests-"))
GALLERY_ROOT = _TMP / "gallery"
SHEET_MUSIC_ROOT = _TMP / "sheet_music"
