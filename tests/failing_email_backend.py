from django.core.mail.backends.base import BaseEmailBackend


class FailingBackend(BaseEmailBackend):
    """Test double that simulates an SMTP outage."""

    def send_messages(self, email_messages):
        raise ConnectionError("simulated SMTP outage")
