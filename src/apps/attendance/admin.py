from django.contrib import admin
from django.http import HttpRequest

from .models import AttendanceResponse


@admin.register(AttendanceResponse)
class AttendanceResponseAdmin(admin.ModelAdmin):
    """Read-only: responses are made by musicians themselves, never edited by admins."""

    list_display = ("event", "user", "status", "updated_at")
    list_filter = ("status", "event")
    search_fields = ("user__email", "event__title")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False
