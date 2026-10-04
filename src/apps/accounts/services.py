"""Account lifecycle use cases."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.common.audit import log_admin_event

from .roles import STAFF_ROLES

User = get_user_model()


class EmailAlreadyUsed(Exception):
    """An account with this e-mail address already exists."""


@transaction.atomic
def create_invited_user(*, email: str, full_name: str, roles: list[str]) -> "User":
    """Create an account without a password; the user sets it through an invitation link."""
    if User.objects.filter(email__iexact=email).exists():
        raise EmailAlreadyUsed(email)
    user = User.objects.create_user(email=email, full_name=full_name)
    groups = Group.objects.filter(name__in=roles)
    user.groups.set(groups)
    refresh_staff_flag(user)
    log_admin_event("account_created", user_id=str(user.pk), roles=sorted(roles))
    return user


def refresh_staff_flag(user: "User") -> None:
    """is_staff follows roles so that musicians never reach the back office."""
    should = user.is_superuser or user.groups.filter(name__in=STAFF_ROLES).exists()
    if user.is_staff != should:
        user.is_staff = should
        user.save(update_fields=["is_staff"])


def build_setup_url(user: "User") -> str:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    path = reverse("accounts:password_reset_confirm", kwargs={"uidb64": uid, "token": token})
    return f"{settings.SITE_URL}{path}"


def send_invitation(user: "User") -> None:
    """E-mail a one-hour password-setup link (uses SITE_URL, never the request Host)."""
    context = {"user": user, "setup_url": build_setup_url(user), "site_name": settings.SITE_NAME}
    message = EmailMultiAlternatives(
        subject=f"Pozvánka do portálu: {settings.SITE_NAME}",
        body=render_to_string("accounts/email/invitation.txt", context),
        to=[user.email],
    )
    message.attach_alternative(render_to_string("accounts/email/invitation.html", context), "text/html")
    message.send()
    log_admin_event("invitation_sent", user_id=str(user.pk))


def set_user_active(user: "User", *, active: bool, actor: "User") -> None:
    if user.is_active == active:
        return
    user.is_active = active
    user.save(update_fields=["is_active"])
    log_admin_event(
        "account_activated" if active else "account_deactivated",
        user_id=str(user.pk),
        actor_id=str(actor.pk),
    )
