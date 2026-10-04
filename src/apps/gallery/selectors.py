from django.db.models import Count, Prefetch, Q, QuerySet

from .models import Album, GalleryImage


def published_albums() -> QuerySet[Album]:
    return (
        Album.objects.filter(is_published=True)
        .annotate(photo_count=Count("images", filter=Q(images__is_published=True)))
        .filter(photo_count__gt=0)
        .prefetch_related(
            Prefetch(
                "images",
                queryset=GalleryImage.objects.filter(is_published=True).order_by("position", "created_at"),
                to_attr="visible_images",
            )
        )
    )


def published_album(slug: str) -> Album | None:
    return published_albums().filter(slug=slug).first()


def preview_images(limit: int = 6) -> list[GalleryImage]:
    return list(
        GalleryImage.objects.filter(is_published=True, album__is_published=True)
        .select_related("album")
        .order_by("-created_at")[:limit]
    )


def public_image(pk) -> GalleryImage | None:
    """Only published images of published albums are deliverable."""
    return (
        GalleryImage.objects.filter(pk=pk, is_published=True, album__is_published=True)
        .select_related("album")
        .first()
    )
