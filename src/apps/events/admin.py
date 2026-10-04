from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.common.admin_actions import confirm_action

from . import services
from .models import Event, EventStatus


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "starts_at", "status", "is_public", "attendance_enabled")
    list_filter = ("kind", "status", "is_public")
    search_fields = ("title", "venue_name")
    date_hierarchy = "starts_at"
    prepopulated_fields = {"slug": ("title",)}
    actions = ["confirm_events", "cancel_events", "publish_events", "unpublish_events"]
    fieldsets = (
        (None, {"fields": ("title", "slug", "kind", "status", "is_public")}),
        ("Čas", {"fields": ("starts_at", "ends_at", "meeting_time")}),
        ("Místo", {"fields": ("venue_name", "venue_address", "map_url")}),
        ("Veřejný obsah", {"fields": ("public_description",)}),
        ("Interní (jen pro členy)", {"fields": ("internal_notes",)}),
        ("Docházka", {"fields": ("attendance_enabled", "attendance_deadline")}),
    )

    def has_delete_permission(self, request: HttpRequest, obj: Event | None = None) -> bool:
        return super().has_delete_permission(request, obj)

    @admin.action(description="Označit jako potvrzené", permissions=["change"])
    def confirm_events(self, request: HttpRequest, queryset: QuerySet) -> None:
        self._change_status(request, queryset, EventStatus.CONFIRMED)

    @admin.action(description="Zrušit vybrané akce", permissions=["change"])
    def cancel_events(self, request: HttpRequest, queryset: QuerySet):
        return confirm_action(
            self,
            request,
            queryset,
            action_name="cancel_events",
            title="Potvrdit zrušení akcí",
            description="Zrušené akce zůstanou veřejně viditelné se stavem „Zrušeno“.",
            perform=lambda event: self._safe(
                request, lambda: services.change_status(event, EventStatus.CANCELLED, actor=request.user)
            ),
            success_message="Zpracováno akcí: {count}.",
        )

    @admin.action(description="Zveřejnit na webu", permissions=["change"])
    def publish_events(self, request: HttpRequest, queryset: QuerySet) -> None:
        for event in queryset:
            self._safe(request, lambda event=event: services.set_public(event, public=True, actor=request.user))

    @admin.action(description="Skrýt z veřejného webu", permissions=["change"])
    def unpublish_events(self, request: HttpRequest, queryset: QuerySet) -> None:
        for event in queryset:
            self._safe(request, lambda event=event: services.set_public(event, public=False, actor=request.user))

    def _change_status(self, request: HttpRequest, queryset: QuerySet, status: str) -> None:
        for event in queryset:
            self._safe(request, lambda event=event: services.change_status(event, status, actor=request.user))

    def _safe(self, request: HttpRequest, operation) -> None:
        try:
            operation()
        except services.EventServiceError as exc:
            self.message_user(request, f"Operaci nelze provést: {exc}", messages.WARNING)
