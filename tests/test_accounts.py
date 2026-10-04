"""Authentication, roles, invitations and object-level portal access."""

import pytest
from django.core import mail
from django.db import IntegrityError, transaction
from django.urls import reverse

from apps.accounts import roles
from apps.accounts.models import User
from apps.accounts.services import build_setup_url, create_invited_user, send_invitation

from .conftest import PASSWORD

pytestmark = pytest.mark.django_db


def test_login_with_email_case_insensitive(client, make_user):
    make_user([roles.MUSICIAN], email="Pavel@Example.test")
    response = client.post(
        reverse("accounts:login"), {"username": "pavel@example.test", "password": PASSWORD}
    )
    assert response.status_code == 302
    assert response.url == reverse("musicians:dashboard")


def test_login_rejects_wrong_password_with_generic_error(client, musician):
    response = client.post(
        reverse("accounts:login"), {"username": musician.email, "password": "spatne"}
    )
    assert response.status_code == 200
    assert b"error-summary" in response.content


def test_inactive_user_cannot_login(client, make_user):
    user = make_user([roles.MUSICIAN], active=False)
    response = client.post(
        reverse("accounts:login"), {"username": user.email, "password": PASSWORD}
    )
    assert response.status_code == 200
    assert "_auth_user_id" not in client.session


def test_email_unique_case_insensitively(make_user):
    make_user(email="a@example.test")
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user(email="A@EXAMPLE.TEST", full_name="Duplicita")


@pytest.mark.parametrize("name", ["musicians:dashboard", "attendance:list", "sheet_music:list"])
def test_portal_redirects_anonymous_to_login(client, name):
    response = client.get(reverse(name))
    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


def test_authenticated_without_portal_permission_gets_403(login, make_user):
    outsider = make_user([], profile=False)
    assert login(outsider).get(reverse("musicians:dashboard")).status_code == 403


def test_musician_has_portal_but_not_back_office(login, musician):
    client = login(musician)
    assert client.get(reverse("musicians:dashboard")).status_code == 200
    assert musician.is_staff is False
    assert client.get(reverse("admin:index")).status_code == 302  # redirected to admin login


def test_staff_roles_set_staff_flag(organizer, editor, admin_user, musician):
    assert organizer.is_staff and editor.is_staff and admin_user.is_staff
    assert not musician.is_staff


def test_role_permissions_are_least_privilege(organizer, editor, musician):
    assert musician.has_perm("accounts.access_portal")
    assert not musician.has_perm("events.add_event")
    assert organizer.has_perm("events.add_event")
    assert not organizer.has_perm("gallery.add_album")
    assert editor.has_perm("gallery.add_album")
    assert not editor.has_perm("events.add_event")
    assert not editor.has_perm("sheet_music.view_piece")
    assert not organizer.has_perm("accounts.add_user")


def test_sync_roles_is_idempotent(db):
    roles.sync_roles()
    roles.sync_roles()
    from django.contrib.auth.models import Group

    assert Group.objects.filter(name__in=roles.ALL_ROLES).count() == len(roles.ALL_ROLES)


def test_create_invited_user_has_unusable_password(db):
    roles.sync_roles()
    user = create_invited_user(email="novy@example.test", full_name="Nový", roles=[roles.MUSICIAN])
    assert not user.has_usable_password()
    assert user.groups.filter(name=roles.MUSICIAN).exists()


def test_invitation_uses_configured_site_url_not_host_header(db, settings):
    roles.sync_roles()
    settings.SITE_URL = "https://kapela.example.test"
    user = create_invited_user(email="novy@example.test", full_name="Nový", roles=[roles.MUSICIAN])
    send_invitation(user)
    assert len(mail.outbox) == 1
    assert "https://kapela.example.test/ucet/heslo/reset/" in mail.outbox[0].body
    assert build_setup_url(user).startswith("https://kapela.example.test/")


def test_password_reset_response_does_not_reveal_account_existence(client, musician):
    known = client.post(reverse("accounts:password_reset"), {"email": musician.email})
    unknown = client.post(reverse("accounts:password_reset"), {"email": "nikdo@example.test"})
    assert known.status_code == unknown.status_code == 302
    assert known.url == unknown.url
    assert len(mail.outbox) == 1


def test_password_reset_token_has_one_hour_timeout(settings):
    assert settings.PASSWORD_RESET_TIMEOUT == 3600


def test_weak_password_is_rejected(login, musician):
    response = login(musician).post(
        reverse("accounts:password_change"),
        {"old_password": PASSWORD, "new_password1": "heslo123", "new_password2": "heslo123"},
    )
    assert response.status_code == 200


def test_logout_requires_post(login, musician):
    client = login(musician)
    assert client.get(reverse("accounts:logout")).status_code == 405
    assert client.post(reverse("accounts:logout")).status_code == 302


def test_repeated_failed_logins_lock_out_even_with_correct_password(client, musician, settings):
    """django-axes is disabled in test settings; enable it here explicitly."""
    from axes.models import AccessAttempt

    settings.AXES_ENABLED = True
    settings.AXES_FAILURE_LIMIT = 3
    url = reverse("accounts:login")
    for _ in range(3):
        client.post(url, {"username": musician.email, "password": "spatne-heslo"})
    locked = client.post(url, {"username": musician.email, "password": PASSWORD})
    assert locked.status_code == 429
    assert "dočasně uzamčen" in locked.content.decode()
    assert "_auth_user_id" not in client.session
    assert AccessAttempt.objects.exists()
