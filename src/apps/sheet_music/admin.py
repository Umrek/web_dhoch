from django.contrib import admin, messages
from django.http import HttpRequest

from . import services
from .models import Piece, SheetMusicPart


class PartInline(admin.TabularInline):
    model = SheetMusicPart
    extra = 0
    fields = ("section", "version", "is_current", "uploaded_at")
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


@admin.register(Piece)
class PieceAdmin(admin.ModelAdmin):
    list_display = ("title", "composer", "arranger", "is_archived")
    list_filter = ("is_archived",)
    search_fields = ("title", "composer", "arranger")
    inlines = [PartInline]
    actions = ["archive_pieces", "unarchive_pieces"]

    @admin.action(description="Archivovat vybrané skladby", permissions=["change"])
    def archive_pieces(self, request: HttpRequest, queryset) -> None:
        self.message_user(request, f"Archivováno: {queryset.update(is_archived=True)}.")

    @admin.action(description="Obnovit z archivu", permissions=["change"])
    def unarchive_pieces(self, request: HttpRequest, queryset) -> None:
        self.message_user(request, f"Obnoveno: {queryset.update(is_archived=False)}.")


@admin.register(SheetMusicPart)
class SheetMusicPartAdmin(admin.ModelAdmin):
    """Upload creates a new version; existing files are immutable (replace = new upload)."""

    list_display = ("piece", "section", "version", "is_current", "size_bytes", "uploaded_at")
    list_filter = ("section", "is_current")
    search_fields = ("piece__title",)
    autocomplete_fields = ("piece",)
    readonly_fields = ("original_name", "size_bytes", "sha256", "version", "uploaded_by", "uploaded_at")

    def get_readonly_fields(self, request: HttpRequest, obj: SheetMusicPart | None = None):
        base = tuple(super().get_readonly_fields(request, obj))
        if obj is not None:
            return (*base, "piece", "section", "file", "copyright_confirmed")
        return base

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return request.user.is_superuser or request.user.has_perm("sheet_music.delete_sheetmusicpart")

    def save_model(self, request: HttpRequest, obj: SheetMusicPart, form, change: bool) -> None:
        if change:
            super().save_model(request, obj, form, change)
            return
        try:
            services.register_upload(obj, actor=request.user)
        except services.CopyrightNotConfirmed:
            self.message_user(request, "Bez potvrzení práv k notám nelze soubor uložit.", messages.ERROR)
