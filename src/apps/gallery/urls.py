from django.urls import path, register_converter

from . import views


class VariantConverter:
    regex = "nahled|plny"

    def to_python(self, value: str) -> str:
        return value

    def to_url(self, value: str) -> str:
        return value


register_converter(VariantConverter, "variant")

app_name = "gallery"

urlpatterns = [
    path("", views.album_list, name="list"),
    path("foto/<uuid:pk>/<variant:variant>/", views.image_file, name="image"),
    path("<slug:slug>/", views.album_detail, name="album"),
]
