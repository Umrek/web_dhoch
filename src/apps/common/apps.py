from django.apps import AppConfig
from django.contrib import admin


class CommonConfig(AppConfig):
    name = "apps.common"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        admin.site.site_header = "Správa webu Oderské chasy"
        admin.site.site_title = "Správa webu"
        admin.site.index_title = "Přehled správy"
        # Bulk "delete selected" is disabled globally; destructive operations are
        # explicit, per-object and go through confirmation pages or domain services.
        admin.site.disable_action("delete_selected")
