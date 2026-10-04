"""Roles are Django Groups with explicit permission sets, synchronised by ``sync_roles``."""

from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ImproperlyConfigured

MUSICIAN = "Muzikant"
CONTENT_EDITOR = "Redaktor obsahu"
EVENT_ORGANIZER = "Organizátor akcí"
ADMINISTRATOR = "Administrátor"

STAFF_ROLES = {CONTENT_EDITOR, EVENT_ORGANIZER, ADMINISTRATOR}
ALL_ROLES = [MUSICIAN, CONTENT_EDITOR, EVENT_ORGANIZER, ADMINISTRATOR]

_CRUD = ("add", "change", "delete", "view")
_ADMIN_APPS = [
    "accounts",
    "content",
    "events",
    "attendance",
    "gallery",
    "musicians",
    "sheet_music",
    "contact",
]


def _perms(app_model: str, *actions: str) -> list[str]:
    app, model = app_model.split(".")
    return [f"{app}.{action}_{model}" for action in actions]


ROLE_PERMISSIONS: dict[str, list[str]] = {
    MUSICIAN: ["accounts.access_portal"],
    CONTENT_EDITOR: [
        *_perms("content.page", *_CRUD),
        *_perms("content.sitesettings", "change", "view"),
        *_perms("content.announcement", *_CRUD),
        *_perms("gallery.album", "add", "change", "view"),
        *_perms("gallery.galleryimage", *_CRUD),
        *_perms("events.event", "view"),
    ],
    EVENT_ORGANIZER: [
        *_perms("events.event", "add", "change", "view"),
        *_perms("attendance.attendanceresponse", "view"),
        *_perms("content.announcement", "add", "change", "view"),
        *_perms("sheet_music.piece", "add", "change", "view"),
        *_perms("sheet_music.sheetmusicpart", "add", "change", "view"),
    ],
    # ADMINISTRATOR receives every permission of the project apps (see sync_roles).
}


def sync_roles() -> None:
    """Create/refresh role groups. Idempotent; run after every migrate (release step)."""
    for name, codes in ROLE_PERMISSIONS.items():
        group, _ = Group.objects.get_or_create(name=name)
        permissions = []
        missing = []
        for code in codes:
            app_label, codename = code.split(".")
            perm = Permission.objects.filter(
                content_type__app_label=app_label, codename=codename
            ).first()
            if perm is None:
                missing.append(code)
            else:
                permissions.append(perm)
        if missing:
            raise ImproperlyConfigured(f"Unknown permissions for role {name}: {missing}")
        group.permissions.set(permissions)

    admin_group, _ = Group.objects.get_or_create(name=ADMINISTRATOR)
    admin_group.permissions.set(Permission.objects.filter(content_type__app_label__in=_ADMIN_APPS))
