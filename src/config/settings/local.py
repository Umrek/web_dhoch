"""Local development settings. NEVER use in production."""

import os
from pathlib import Path

from .base import *  # noqa: F403
from .base import REPO_DIR
from .env import get_bool, get_str, parse_database_url


def _load_dotenv(path: Path) -> None:
    """Minimal .env reader for local development (existing variables win)."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(REPO_DIR / ".env")

DEBUG = get_bool("DEBUG", True)
# Marked insecure on purpose; production refuses this value.
SECRET_KEY = get_str("SECRET_KEY", "insecure-local-development-key-do-not-deploy")
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

_db_url = get_str("DATABASE_URL", f"sqlite:///{REPO_DIR / 'db.sqlite3'}") or ""
DATABASES = {"default": parse_database_url(_db_url)}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
STATICFILES_DIRS = [Path(__file__).resolve().parents[2] / "static"]
