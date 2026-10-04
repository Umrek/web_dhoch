"""Security headers, CSRF, error pages, admin hardening and production configuration."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.contrib import admin
from django.test import Client
from django.urls import reverse

SRC = Path(__file__).resolve().parents[1] / "src"

pytestmark = pytest.mark.django_db


def test_security_headers_present(client):
    response = client.get(reverse("content:home"))
    assert response["X-Content-Type-Options"] == "nosniff"
    csp = response["Content-Security-Policy"]
    assert "default-src" in csp
    assert "unsafe-eval" not in csp
    assert "script-src 'unsafe-inline'" not in csp
    assert "frame-ancestors 'none'" in csp
    assert response["X-Frame-Options"] == "DENY"


def test_no_inline_scripts_or_handlers_in_templates():
    root = SRC / "templates"
    offenders = []
    for path in root.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        if "<script>" in lowered or " onclick=" in lowered or " onload=" in lowered or "javascript:" in lowered:
            offenders.append(str(path))
        if "<script" in lowered and "src=" not in lowered:
            offenders.append(str(path))
    assert not offenders


def test_all_post_forms_include_csrf_token():
    root = SRC / "templates"
    for path in root.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        if 'method="post"' in text:
            assert "{% csrf_token %}" in text, path


def test_csrf_is_enforced_on_login_and_profile_post(make_user):
    strict = Client(enforce_csrf_checks=True)
    assert strict.post(reverse("accounts:login"), {"username": "a", "password": "b"}).status_code == 403
    user = make_user(["Muzikant"])
    strict.force_login(user)
    assert strict.post(reverse("musicians:profile"), {"display_name": "x"}).status_code == 403


def test_custom_error_pages(client):
    response = client.get("/neexistuje/")
    assert response.status_code == 404
    assert "Stránka nenalezena" in response.content.decode()


def test_error_page_does_not_leak_debug_info(client):
    assert b"Traceback" not in client.get("/neexistuje/").content


def test_bulk_delete_action_is_disabled_globally():
    assert "delete_selected" not in admin.site._actions


def test_admin_requires_staff(client, login, musician, admin_user):
    assert client.get(reverse("admin:index")).status_code == 302
    assert login(musician).get(reverse("admin:index")).status_code == 302
    client.logout()
    assert login(admin_user).get(reverse("admin:index")).status_code == 200


def test_attendance_admin_is_read_only(admin_user, rf):
    from apps.attendance.admin import AttendanceResponseAdmin
    from apps.attendance.models import AttendanceResponse

    model_admin = AttendanceResponseAdmin(AttendanceResponse, admin.site)
    request = rf.get("/")
    request.user = admin_user
    assert not model_admin.has_add_permission(request)
    assert not model_admin.has_change_permission(request)
    assert not model_admin.has_delete_permission(request)


def test_cookie_defaults_are_hardened(settings):
    assert settings.SESSION_COOKIE_HTTPONLY is True
    assert settings.SESSION_COOKIE_SAMESITE == "Lax"
    assert settings.CSRF_COOKIE_SAMESITE == "Lax"


def test_no_media_url_is_configured(settings):
    assert not getattr(settings, "MEDIA_URL", "")


def test_secret_key_not_hardcoded_in_base_or_production():
    for name in ("base.py", "production.py"):
        text = (SRC / "config" / "settings" / name).read_text(encoding="utf-8")
        assert "SECRET_KEY =" not in text or "require_str" in text


# --- production settings are validated in a clean interpreter ---------------------------

VALID_ENV = {
    "DJANGO_SETTINGS_MODULE": "config.settings.production",
    "SECRET_KEY": "k" * 8 + "Zq7vX2mP9sLw4RtYb6NcHd3JfGa8UeKi5OoVn1MxBzCyDuAh",
    "ALLOWED_HOSTS": "kapela.example.test",
    "CSRF_TRUSTED_ORIGINS": "https://kapela.example.test",
    "SITE_URL": "https://kapela.example.test",
    "DATABASE_URL": "postgresql://user:pw@db:5432/app",
    "EMAIL_HOST": "smtp.example.test",
    "DEFAULT_FROM_EMAIL": "Kapela <web@example.test>",
    "ADMIN_CONTACT_EMAIL": "admin@example.test",
    "PRIVACY_CONTACT_EMAIL": "gdpr@example.test",
    "SECURITY_CONTACT_EMAIL": "security@example.test",
    "CONTACT_RECIPIENT_EMAIL": "kapela@example.test",
}


def run_production(overrides=None, remove=()):
    env = {k: v for k, v in os.environ.items() if k not in VALID_ENV}
    env.update(VALID_ENV)
    env.update(overrides or {})
    for key in remove:
        env.pop(key, None)
    code = (
        "import config.settings.production as s;"
        "print(s.SESSION_COOKIE_NAME, s.SECURE_SSL_REDIRECT, s.DEBUG)"
    )
    return subprocess.run(  # noqa: S603
        [sys.executable, "-c", code], cwd=SRC, env=env, capture_output=True, text=True, check=False
    )


def test_production_settings_load_with_valid_environment():
    result = run_production()
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["__Host-sessionid", "True", "False"]


@pytest.mark.parametrize(
    ("overrides", "remove"),
    [
        ({}, ["SECRET_KEY"]),
        ({"SECRET_KEY": "short"}, []),
        ({"SECRET_KEY": "insecure-" + "x" * 60}, []),
        ({"ALLOWED_HOSTS": "*"}, []),
        ({}, ["ALLOWED_HOSTS"]),
        ({"CSRF_TRUSTED_ORIGINS": "http://kapela.example.test"}, []),
        ({"SITE_URL": "http://kapela.example.test"}, []),
        ({"DATABASE_URL": "sqlite:///db.sqlite3"}, []),
        ({}, ["EMAIL_HOST"]),
        ({}, ["DATABASE_URL"]),
    ],
)
def test_production_fails_fast_on_insecure_configuration(overrides, remove):
    result = run_production(overrides, remove)
    assert result.returncode != 0
    assert "ImproperlyConfigured" in result.stderr
