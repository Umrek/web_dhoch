"""Management commands, migrations consistency and demo data."""

import pytest
from django.contrib.auth.models import Group
from django.core.management import CommandError, call_command

from apps.accounts import roles

pytestmark = pytest.mark.django_db


def test_migrations_are_in_sync_with_models():
    """Hand-written migrations must match the models: no pending changes allowed."""
    call_command("makemigrations", "--check", "--dry-run", verbosity=0)


def test_django_system_checks_pass():
    call_command("check")


def test_sync_roles_command_creates_all_groups_and_admin_has_all_project_perms():
    call_command("sync_roles")
    assert set(Group.objects.values_list("name", flat=True)) >= set(roles.ALL_ROLES)
    admin_group = Group.objects.get(name=roles.ADMINISTRATOR)
    assert admin_group.permissions.filter(codename="access_portal").exists()
    assert admin_group.permissions.filter(codename="delete_event").exists()


def test_demo_data_refuses_to_run_without_debug(settings):
    settings.DEBUG = False
    with pytest.raises(CommandError):
        call_command("load_demo_data")


def test_demo_data_is_idempotent_and_fictional(settings):
    settings.DEBUG = True
    call_command("load_demo_data", "--password", "Demo-Heslo-Jen-Pro-Test-1")
    call_command("load_demo_data", "--password", "Demo-Heslo-Jen-Pro-Test-1")
    from apps.accounts.models import User
    from apps.events.models import Event
    from apps.gallery.models import GalleryImage
    from apps.sheet_music.models import SheetMusicPart

    assert User.objects.count() == 5
    assert all(email.endswith("@demo.invalid") for email in User.objects.values_list("email", flat=True))
    assert Event.objects.filter(slug="demo-zkouska", is_public=False).exists()
    assert GalleryImage.objects.count() == 1
    assert SheetMusicPart.objects.count() == 1
    assert User.objects.get(email="admin@demo.invalid").is_staff
    assert not User.objects.get(email="muzikant1@demo.invalid").is_staff
