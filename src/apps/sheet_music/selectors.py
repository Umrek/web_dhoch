from django.db.models import Prefetch, Q, QuerySet

from .models import Piece, SheetMusicPart


def visible_pieces(*, query: str = "", section: str = "") -> QuerySet[Piece]:
    """Non-archived pieces with only their current parts (optionally one section)."""
    parts = SheetMusicPart.objects.filter(is_current=True)
    if section:
        parts = parts.filter(section=section)
    pieces = Piece.objects.filter(is_archived=False).prefetch_related(
        Prefetch("parts", queryset=parts.order_by("section"), to_attr="current_parts")
    )
    if query:
        pieces = pieces.filter(
            Q(title__icontains=query) | Q(composer__icontains=query) | Q(arranger__icontains=query)
        )
    if section:
        pieces = pieces.filter(parts__is_current=True, parts__section=section)
    return pieces.distinct()


def downloadable_part(pk: int) -> SheetMusicPart | None:
    """Members may fetch only current parts of non-archived pieces."""
    return (
        SheetMusicPart.objects.select_related("piece")
        .filter(pk=pk, is_current=True, piece__is_archived=False)
        .first()
    )
