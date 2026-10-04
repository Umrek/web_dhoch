from django.contrib import admin

from .models import MusicianProfile


@admin.register(MusicianProfile)
class MusicianProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "section", "instrument", "public_listing", "is_active_member")
    list_filter = ("section", "public_listing", "is_active_member")
    search_fields = ("display_name", "user__email")
    autocomplete_fields = ("user",)
    readonly_fields = ("public_listing_changed_at",)
