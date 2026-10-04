import re
import uuid
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from .logging import request_id_var

_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")

PERMISSIONS_POLICY = "camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()"


class RequestIDMiddleware:
    """Attach a correlation id to each request (sanitised client value or new UUID)."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        incoming = request.headers.get("X-Request-ID", "")
        request_id = incoming if _VALID_REQUEST_ID.match(incoming) else uuid.uuid4().hex
        request.request_id = request_id  # type: ignore[attr-defined]
        token = request_id_var.set(request_id)
        try:
            response = self.get_response(request)
        finally:
            request_id_var.reset(token)
        response["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware:
    """Headers not covered by Django's SecurityMiddleware."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        response.setdefault("Permissions-Policy", PERMISSIONS_POLICY)
        response.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        return response
