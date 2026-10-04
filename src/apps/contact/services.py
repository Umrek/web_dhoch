import hashlib
import logging

from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.http import HttpRequest

from apps.common.audit import log_security_event

from .models import ContactMessage

logger = logging.getLogger(__name__)


class RateLimited(Exception):
    pass


def client_ip(request: HttpRequest) -> str:
    """Client address behind ``AXES_IPWARE_PROXY_COUNT`` trusted proxies (0 = no proxy).

    Only the entry appended by our own outermost proxy is trusted; client-supplied
    X-Forwarded-For prefixes are ignored, so the value cannot be spoofed to dodge limits.
    """
    proxies = getattr(settings, "AXES_IPWARE_PROXY_COUNT", 0) or 0
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if proxies and forwarded:
        hops = [part.strip() for part in forwarded.split(",") if part.strip()]
        if len(hops) >= proxies:
            return hops[-proxies]
    return request.META.get("REMOTE_ADDR", "")


def _client_key(request: HttpRequest) -> str:
    raw = f"{client_ip(request)}|{settings.SECRET_KEY}"
    return "contact-rl:" + hashlib.sha256(raw.encode()).hexdigest()


def check_rate_limit(request: HttpRequest) -> None:
    """Fixed-window counter keyed by a salted hash (no raw IP is stored anywhere)."""
    key = _client_key(request)
    if cache.add(key, 1, timeout=settings.CONTACT_RATE_WINDOW_SECONDS):
        return
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=settings.CONTACT_RATE_WINDOW_SECONDS)
        return
    if count > settings.CONTACT_RATE_LIMIT:
        log_security_event("contact_rate_limited")
        raise RateLimited


def submit_message(*, name: str, email: str, message: str) -> ContactMessage:
    """Store the message, then notify by e-mail; delivery failure never loses the message."""
    record = ContactMessage.objects.create(name=name, email=email, message=message)
    mail = EmailMessage(
        subject="Nová zpráva z webu kapely",
        body=f"Od: {name} <{email}>\n\n{message}\n",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.CONTACT_RECIPIENT_EMAIL],
        reply_to=[email],
    )
    try:
        mail.send(fail_silently=False)
    except Exception:
        logger.exception("Contact e-mail delivery failed", extra={"message_id": record.pk})
    else:
        record.email_sent = True
        record.save(update_fields=["email_sent"])
    return record
