from django.urls import path

from . import views

app_name = "content"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("o-nas/", views.AboutView.as_view(), name="about"),
    path("pravni/<slug:slug>/", views.LegalPageView.as_view(), name="legal"),
    path("robots.txt", views.RobotsTxtView.as_view(), name="robots"),
    path(".well-known/security.txt", views.SecurityTxtView.as_view(), name="security_txt"),
]
