from django.urls import path

from . import views

app_name = "attendance"

urlpatterns = [
    path("akce/", views.MemberEventListView.as_view(), name="list"),
    path("akce/<slug:slug>/", views.MemberEventDetailView.as_view(), name="detail"),
    path("akce/<slug:slug>/prehled/", views.EventOverviewView.as_view(), name="overview"),
]
