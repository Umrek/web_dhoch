from django.contrib import admin
from django.http import HttpRequest

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at", "email_sent", "is_handled")
    list_filter = ("is_handled", "email_sent")
    search_fields = ("name", "email")
    readonly_fields = ("name", "email", "message", "consent_given_at", "email_sent", "created_at")
    actions = ["mark_handled"]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    @admin.action(description="Označit jako vyřízené", permissions=["change"])
    def mark_handled(self, request: HttpRequest, queryset) -> None:
        self.message_user(request, f"Vyřízeno: {queryset.update(is_handled=True)}.")
