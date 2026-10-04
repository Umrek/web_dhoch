"""Root URL configuration."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("health/", include("apps.common.urls")),
    path(settings.ADMIN_URL, admin.site.urls),
    path("ucet/", include("apps.accounts.urls")),
    path("portal/", include("apps.musicians.urls")),
    path("portal/", include("apps.attendance.urls")),
    path("portal/noty/", include("apps.sheet_music.urls")),
    path("akce/", include("apps.events.urls")),
    path("galerie/", include("apps.gallery.urls")),
    path("kontakt/", include("apps.contact.urls")),
    path("", include("apps.content.urls")),
]
