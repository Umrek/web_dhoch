from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("prihlaseni/", views.LoginView.as_view(), name="login"),
    path("odhlaseni/", LogoutView.as_view(), name="logout"),
    path("heslo/zmena/", views.PasswordChangeView.as_view(), name="password_change"),
    path("heslo/zmena/hotovo/", views.PasswordChangeDoneView.as_view(), name="password_change_done"),
    path("heslo/reset/", views.PasswordResetView.as_view(), name="password_reset"),
    path("heslo/reset/odeslano/", views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path(
        "heslo/reset/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "heslo/reset/hotovo/",
        views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
