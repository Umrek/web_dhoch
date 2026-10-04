import uuid

from django.core.files.base import ContentFile
from django.db import transaction

from apps.common.audit import log_admin_event
from apps.common.storage import gallery_storage

from .images import ProcessedImage
from .models import Album, GalleryImage


def store_image(image: GalleryImage, processed: ProcessedImage, *, actor) -> GalleryImage:
    """Persist processed bytes under generated names, then save the row (rollback on failure)."""
    storage = gallery_storage()
    token = uuid.uuid4().hex
    full_name = storage.save(f"{token}.jpg", ContentFile(processed.full))
    thumb_name = storage.save(f"{token}_t.jpg", ContentFile(processed.thumbnail))
    image.image.name = full_name
    image.thumbnail.name = thumb_name
    image.width, image.height = processed.width, processed.height
    image.uploaded_by = actor
    try:
        image.save()
    except Exception:
        storage.delete(full_name)
        storage.delete(thumb_name)
        raise
    log_admin_event(
        "gallery_image_uploaded", image_id=str(image.pk), actor_id=str(getattr(actor, "pk", ""))
    )
    return image


def delete_image_files(image: GalleryImage) -> None:
    storage = gallery_storage()
    for name in (image.image.name, image.thumbnail.name):
        if name:
            storage.delete(name)


@transaction.atomic
def delete_image(image: GalleryImage, *, actor) -> None:
    pk = str(image.pk)
    delete_image_files(image)
    image.delete()
    log_admin_event("gallery_image_deleted", image_id=pk, actor_id=str(getattr(actor, "pk", "")))


@transaction.atomic
def delete_album(album: Album, *, actor) -> None:
    for image in album.images.all():
        delete_image_files(image)
    pk = album.pk
    album.delete()
    log_admin_event("gallery_album_deleted", album_id=pk, actor_id=str(getattr(actor, "pk", "")))
