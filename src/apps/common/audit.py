"""Minimal security/administrative audit logging (stdout, never secrets or personal data)."""

import logging

_logger = logging.getLogger("security")


def log_security_event(event: str, *, level: int = logging.WARNING, **fields: object) -> None:
    """Log a security-relevant event.

    Pass identifiers (user id, object id), never e-mail addresses, IP addresses,
    passwords, tokens, message bodies or file contents.
    """
    _logger.log(level, event, extra={"event_fields": {"event": event, **fields}})


def log_admin_event(event: str, **fields: object) -> None:
    log_security_event(event, level=logging.INFO, **fields)
