from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpRequest, HttpResponseRedirect

from apps.common.audit import log_security_event


class PortalRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """Anonymous -> login redirect; authenticated without portal permission -> 403."""

    permission_required = "accounts.access_portal"
    request: HttpRequest

    def handle_no_permission(self) -> HttpResponseRedirect:
        user = self.request.user
        if user.is_authenticated:
            log_security_event("portal_access_denied", user_id=str(user.pk), path=self.request.path)
        return super().handle_no_permission()


class PermissionDeniedLoggedMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """Generic permission mixin that logs denials for authenticated users."""

    request: HttpRequest

    def handle_no_permission(self) -> HttpResponseRedirect:
        user = self.request.user
        if user.is_authenticated:
            log_security_event("permission_denied", user_id=str(user.pk), path=self.request.path)
        return super().handle_no_permission()
