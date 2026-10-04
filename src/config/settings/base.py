"""Settings shared by all environments. Environment specifics live in local/test/production."""

from datetime import timedelta
from pathlib import Path

from csp.constants import NONE, SELF

from .env import get_int, get_list, get_str

SRC_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = SRC_DIR.parent

# SECRET_KEY, DEBUG, ALLOWED_HOSTS, DATABASES are deliberately NOT defined here:
# each environment module must set them explicitly (no silent insecure fallback).

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "axes",
    "csp",
    "apps.common",
    "apps.accounts",
    "apps.content",
    "apps.events",
    "apps.musicians",
    "apps.attendance",
    "apps.gallery",
    "apps.sheet_music",
    "apps.contact",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "apps.common.middleware.RequestIDMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "csp.middleware.CSPMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "axes.middleware.AxesMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.common.middleware.SecurityHeadersMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [SRC_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.common.context_processors.site",
            ],
        },
    },
]

AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "musicians:dashboard"
LOGOUT_REDIRECT_URL = "content:home"
PASSWORD_RESET_TIMEOUT = 3600  # seconds; also the lifetime of invitation links

# Login protection (django-axes). Locks on IP and on account separately.
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=15)
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = ["ip_address", "username"]
AXES_LOCKOUT_TEMPLATE = "accounts/lockout.html"
AXES_VERBOSE = False
AXES_IPWARE_PROXY_COUNT = 0

LANGUAGE_CODE = "cs"
TIME_ZONE = "Europe/Prague"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

STATIC_URL = "static/"
STATIC_ROOT = REPO_DIR / "staticfiles"
STATICFILES_DIRS = [SRC_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Files are stored outside any web-served directory and are only delivered by
# authorization-checking views. There is intentionally no MEDIA_URL.
GALLERY_ROOT = Path(get_str("GALLERY_ROOT", str(REPO_DIR / "var" / "gallery")) or "")
SHEET_MUSIC_ROOT = Path(get_str("SHEET_MUSIC_ROOT", str(REPO_DIR / "var" / "sheet_music")) or "")
MAX_SHEET_MUSIC_BYTES = get_int("MAX_SHEET_MUSIC_BYTES", 15 * 1024 * 1024)
MAX_IMAGE_BYTES = get_int("MAX_IMAGE_BYTES", 10 * 1024 * 1024)
MAX_IMAGE_PIXELS = 50_000_000
IMAGE_MAX_DIMENSION = 2400
IMAGE_THUMBNAIL_DIMENSION = 480
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
FILE_UPLOAD_PERMISSIONS = 0o640
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o750

# Site identity and contacts (placeholders unless configured).
SITE_NAME = "Dechová hudba Oderské chasy"
SITE_URL = (get_str("SITE_URL", "http://127.0.0.1:8000") or "").rstrip("/")
ADMIN_CONTACT_EMAIL = get_str("ADMIN_CONTACT_EMAIL", "admin@example.invalid")
PRIVACY_CONTACT_EMAIL = get_str("PRIVACY_CONTACT_EMAIL", "gdpr@example.invalid")
SECURITY_CONTACT_EMAIL = get_str("SECURITY_CONTACT_EMAIL", "security@example.invalid")
CONTACT_RECIPIENT_EMAIL = get_str("CONTACT_RECIPIENT_EMAIL", "kapela@example.invalid")
CONTACT_RETENTION_DAYS = get_int("CONTACT_RETENTION_DAYS", 90)
DEFAULT_FROM_EMAIL = get_str("DEFAULT_FROM_EMAIL", "Oderské chasy <web@example.invalid>")
ADMIN_URL = get_str("ADMIN_URL", "admin/") or "admin/"

# Contact form anti-spam
CONTACT_MIN_FILL_SECONDS = 3
CONTACT_MAX_AGE_SECONDS = 3600
CONTACT_RATE_LIMIT = 5  # messages per window per (hashed) client
CONTACT_RATE_WINDOW_SECONDS = 3600

# Secure cookies and headers (production tightens these further).
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
CSRF_COOKIE_HTTPONLY = False  # Django templates read the token from the form, cookie stays default
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
CSRF_FAILURE_VIEW = "django.views.csrf.csrf_failure"

# Content Security Policy (django-csp 4.x). No inline scripts/styles, no third parties.
# style-src-attr allows only style="" attributes, required by some Django admin widgets.
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": [SELF],
        "script-src": [SELF],
        "style-src": [SELF],
        "style-src-attr": ["'unsafe-inline'"],
        "img-src": [SELF, "data:"],
        "font-src": [SELF],
        "connect-src": [SELF],
        "object-src": [NONE],
        "frame-src": [NONE],
        "frame-ancestors": [NONE],
        "base-uri": [SELF],
        "form-action": [SELF],
    }
}

LOG_LEVEL = (get_str("LOG_LEVEL", "INFO") or "INFO").upper()
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"request_id": {"()": "apps.common.logging.RequestIDFilter"}},
    "formatters": {"json": {"()": "apps.common.logging.JsonFormatter"}},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "json",
            "filters": ["request_id"],
        }
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "security": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "axes": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "django.server": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
ALLOWED_HOSTS = get_list("ALLOWED_HOSTS")
