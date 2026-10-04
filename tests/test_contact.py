"""Contact form: anti-spam, consent, rate limiting, delivery, retention."""

from datetime import timedelta

import pytest
from django.core import mail
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from apps.contact.forms import issue_token
from apps.contact.models import ContactMessage

pytestmark = pytest.mark.django_db


def payload(**overrides):
    data = {
        "name": "Jana Nováková",
        "email": "jana@example.test",
        "message": "Dobrý den, zajímá nás vystoupení.",
        "consent": "on",
        "website": "",
        "token": issue_token(),
    }
    data.update(overrides)
    return data


@pytest.fixture(autouse=True)
def _no_fill_delay(settings):
    settings.CONTACT_MIN_FILL_SECONDS = 0


def test_valid_submission_is_stored_and_emailed(client, settings):
    response = client.post(reverse("contact:form"), payload())
    assert response.status_code == 302
    assert response.url == reverse("contact:thanks")
    record = ContactMessage.objects.get()
    assert record.email_sent is True
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [settings.CONTACT_RECIPIENT_EMAIL]
    assert mail.outbox[0].reply_to == ["jana@example.test"]


def test_header_injection_attempt_is_rejected(client):
    response = client.post(reverse("contact:form"), payload(email="a@example.test\nBcc: x@example.test"))
    assert response.status_code == 400
    assert ContactMessage.objects.count() == 0


def test_consent_is_required(client):
    response = client.post(reverse("contact:form"), payload(consent=""))
    assert response.status_code == 400
    assert ContactMessage.objects.count() == 0


def test_honeypot_looks_successful_but_stores_nothing(client):
    response = client.post(reverse("contact:form"), payload(website="http://spam.example"))
    assert response.status_code == 302
    assert ContactMessage.objects.count() == 0
    assert mail.outbox == []


def test_too_fast_submission_rejected(client, settings):
    settings.CONTACT_MIN_FILL_SECONDS = 60
    response = client.post(reverse("contact:form"), payload())
    assert response.status_code == 400
    assert ContactMessage.objects.count() == 0


def test_tampered_or_missing_token_rejected(client):
    assert client.post(reverse("contact:form"), payload(token="falesny")).status_code == 400
    assert client.post(reverse("contact:form"), payload(token="")).status_code == 400


def test_rate_limit_per_client(client, settings):
    settings.CONTACT_RATE_LIMIT = 2
    codes = [client.post(reverse("contact:form"), payload()).status_code for _ in range(4)]
    assert codes[:2] == [302, 302]
    assert codes[-1] == 429
    assert ContactMessage.objects.count() == 2


def test_email_failure_does_not_lose_message(client, settings):
    settings.EMAIL_BACKEND = "tests.failing_email_backend.FailingBackend"
    assert client.post(reverse("contact:form"), payload()).status_code == 302
    assert ContactMessage.objects.get().email_sent is False


def test_form_get_contains_token_and_hidden_honeypot(client):
    html = client.get(reverse("contact:form")).content.decode()
    assert 'name="token"' in html
    assert 'class="hp-field"' in html
    assert 'aria-hidden="true"' in html


def test_purge_deletes_only_expired_messages(settings):
    settings.CONTACT_RETENTION_DAYS = 30
    old = ContactMessage.objects.create(name="Stará", email="a@example.test", message="x")
    new = ContactMessage.objects.create(name="Nová", email="b@example.test", message="y")
    ContactMessage.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=31))
    call_command("purge_contact_messages", "--dry-run")
    assert ContactMessage.objects.count() == 2
    call_command("purge_contact_messages")
    assert list(ContactMessage.objects.values_list("pk", flat=True)) == [new.pk]


def test_no_ip_address_is_stored():
    names = {f.name for f in ContactMessage._meta.get_fields()}
    assert not {"ip", "ip_address", "user_agent"} & names


@pytest.mark.parametrize(
    ("proxies", "forwarded", "remote", "expected"),
    [
        (0, "6.6.6.6", "10.0.0.1", "10.0.0.1"),  # no proxy configured: header ignored
        (1, "203.0.113.5", "10.0.0.1", "203.0.113.5"),  # one trusted proxy
        (1, "6.6.6.6, 203.0.113.5", "10.0.0.1", "203.0.113.5"),  # spoofed prefix ignored
        (2, "203.0.113.5", "10.0.0.1", "10.0.0.1"),  # too few hops: fall back
    ],
)
def test_client_ip_trusts_only_configured_proxies(rf, settings, proxies, forwarded, remote, expected):
    from apps.contact.services import client_ip

    settings.AXES_IPWARE_PROXY_COUNT = proxies
    request = rf.post("/", HTTP_X_FORWARDED_FOR=forwarded, REMOTE_ADDR=remote)
    assert client_ip(request) == expected


def test_rate_limit_is_per_client_behind_proxy(client, settings):
    settings.CONTACT_RATE_LIMIT = 1
    settings.AXES_IPWARE_PROXY_COUNT = 1
    url = reverse("contact:form")
    assert client.post(url, payload(), HTTP_X_FORWARDED_FOR="203.0.113.1").status_code == 302
    assert client.post(url, payload(), HTTP_X_FORWARDED_FOR="203.0.113.1").status_code == 429
    assert client.post(url, payload(), HTTP_X_FORWARDED_FOR="203.0.113.2").status_code == 302
