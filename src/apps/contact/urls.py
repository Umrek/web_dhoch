from django.urls import path

from . import views

app_name = "contact"

urlpatterns = [
    path("", views.contact, name="form"),
    path("dekujeme/", views.thanks, name="thanks"),
]
