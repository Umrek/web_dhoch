"""Production settings. Every critical value must be provided; nothing falls back."""

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import MIDDLEWARE, SITE_URL
from .env import get_bool, get_int, get_list, get_str, parse_database_url, require_str

DEBUG = False

SECRET_KEY = require_str("SECRET_KEY")
if (
    len(SECRET_KEY) < 50
    or SECRET_KEY.lower().startswith(("insecure", "local-development", "test-only"))
    or "change-me" in SECRET_KEY.lower()
):
    raise ImproperlyConfigured("SECRET_KEY is too short or looks like a development placeholder.")
SECRET_KEY_FALLBACKS = get_list("SECRET_KEY_FALLBACKS")

ALLOWED_HOSTS = get_list("ALLOWED_HOSTS")
if not ALLOWED_HOSTS or any(host in {"*", ".*"} for host in ALLOWED_HOSTS):
    raise ImproperlyConfigured("ALLOWED_HOSTS must list exact host names (no wildcard).")

CSRF_TRUSTED_ORIGINS = get_list("CSRF_TRUSTED_ORIGINS")
if not CSRF_TRUSTED_ORIGINS or not all(o.startswith("https://") for o in CSRF_TRUSTED_ORIGINS):
    raise ImproperlyConfigured("CSRF_TRUSTED_ORIGINS must list https:// origins.")

if not SITE_URL.startswith("https://"):
    raise ImproperlyConfigured("SITE_URL must be the canonical https:// URL.")

_database_url = require_str("DATABASE_URL")
_db = parse_database_url(_database_url)
if "postgresql" not in str(_db["ENGINE"]):
    raise ImproperlyConfigured("Production requires PostgreSQL in DATABASE_URL.")
DATABASES = {"default": _db}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = require_str("EMAIL_HOST")
EMAIL_PORT = get_int("EMAIL_PORT", 587)
EMAIL_HOST_USER = get_str("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = get_str("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = get_bool("EMAIL_USE_TLS", True)
EMAIL_TIMEOUT = 10
for _name in ("DEFAULT_FROM_EMAIL", "ADMIN_CONTACT_EMAIL", "PRIVACY_CONTACT_EMAIL"):
    require_str(_name)
SERVER_EMAIL = DEFAULT_FROM_EMAIL  # noqa: F405
ADMINS = [("Správce webu", ADMIN_CONTACT_EMAIL)]  # noqa: F405

# Cookies and transport
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_NAME = "__Host-sessionid"
CSRF_COOKIE_NAME = "__Host-csrftoken"
SECURE_SSL_REDIRECT = get_bool("SECURE_SSL_REDIRECT", True)
SECURE_REDIRECT_EXEMPT = [r"^health/"]
if get_bool("TRUST_PROXY_SSL_HEADER", True):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = get_int("HSTS_SECONDS", 3600)
SECURE_HSTS_INCLUDE_SUBDOMAINS = get_bool("HSTS_INCLUDE_SUBDOMAINS", False)
SECURE_HSTS_PRELOAD = get_bool("HSTS_PRELOAD", False)
AXES_IPWARE_PROXY_COUNT = get_int("PROXY_COUNT", 1)
AXES_IPWARE_META_PRECEDENCE_ORDER = ["HTTP_X_FORWARDED_FOR", "REMOTE_ADDR"]

CONTENT_SECURITY_POLICY["DIRECTIVES"]["upgrade-insecure-requests"] = True  # noqa: F405

# Static files (WhiteNoise) and shared cache (rate limiting across workers)
MIDDLEWARE = [MIDDLEWARE[0], "whitenoise.middleware.WhiteNoiseMiddleware", *MIDDLEWARE[1:]]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
    }
}
