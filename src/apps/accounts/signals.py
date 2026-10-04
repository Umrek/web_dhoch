"""Non-critical signal receivers (documented in docs/architecture.md)."""

from typing import Any

from apps.common.audit import log_security_event


def log_lockout(sender: object, **kwargs: Any) -> None:
    # Deliberately logs no username, e-mail or IP address.
    log_security_event("login_lockout")
