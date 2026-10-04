from django import forms
from django.contrib import admin
from django.http import HttpRequest

from . import services
from .images import process_image
from .models import Album, GalleryImage


class GalleryImageForm(forms.ModelForm):
    upload = forms.FileField(
        label="Fotografie (JPEG, PNG, WebP)",
        required=False,
        help_text="Metadata (EXIF, GPS) se při nahrání odstraní. Nahrávejte jen fotografie, k nimž máte práva.",
    )

    class Meta:
        model = GalleryImage
        fields = ["album", "alt_text", "caption", "position", "is_published"]

    def clean(self):
        cleaned = super().clean()
        upload = cleaned.get("upload")
        if self.instance._state.adding and not upload:
            self.add_error("upload", "Vyberte soubor s fotografií.")
        if upload:
            self.processed = process_image(upload)  # raises ValidationError on bad input
        return cleaned


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ("title", "happened_on", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}

    def delete_model(self, request: HttpRequest, obj: Album) -> None:
        services.delete_album(obj, actor=request.user)

    def delete_queryset(self, request: HttpRequest, queryset) -> None:
        for album in queryset:
            services.delete_album(album, actor=request.user)


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    form = GalleryImageForm
    list_display = ("alt_text", "album", "position", "is_published", "created_at")
    list_filter = ("album", "is_published")
    search_fields = ("alt_text", "caption")
    fields = ("album", "upload", "alt_text", "caption", "position", "is_published")

    def get_form(self, request: HttpRequest, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return form

    def save_model(self, request: HttpRequest, obj: GalleryImage, form, change: bool) -> None:
        processed = getattr(form, "processed", None)
        if processed is not None:
            if change:
                services.delete_image_files(obj)
            services.store_image(obj, processed, actor=request.user)
        else:
            super().save_model(request, obj, form, change)

    def delete_model(self, request: HttpRequest, obj: GalleryImage) -> None:
        services.delete_image(obj, actor=request.user)

    def delete_queryset(self, request: HttpRequest, queryset) -> None:
        for image in queryset:
            services.delete_image(image, actor=request.user)
