from django.contrib import admin
from django.http import HttpRequest

from .models import Announcement, Page, SiteSettings


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "key", "needs_legal_review", "updated_at")
    list_filter = ("needs_legal_review",)
    search_fields = ("title", "body")


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request: HttpRequest) -> bool:
        return not SiteSettings.objects.exists() and super().has_add_permission(request)

    def has_delete_permission(self, request: HttpRequest, obj: SiteSettings | None = None) -> bool:
        return False


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "published_at", "expires_at", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "body")

    def save_model(self, request: HttpRequest, obj: Announcement, form, change: bool) -> None:
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
