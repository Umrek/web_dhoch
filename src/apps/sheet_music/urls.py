from django.urls import path

from . import views

app_name = "sheet_music"

urlpatterns = [
    path("", views.PieceListView.as_view(), name="list"),
    path("hlas/<int:pk>/stahnout/", views.PartDownloadView.as_view(), name="download"),
]
