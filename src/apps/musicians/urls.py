from django.urls import path

from . import views

app_name = "musicians"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("profil/", views.ProfileView.as_view(), name="profile"),
]
