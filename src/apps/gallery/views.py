from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from . import selectors


@require_GET
def album_list(request: HttpRequest) -> HttpResponse:
    return render(request, "gallery/list.html", {"albums": selectors.published_albums()})


@require_GET
def album_detail(request: HttpRequest, slug: str) -> HttpResponse:
    album = selectors.published_album(slug)
    if album is None:
        raise Http404
    return render(request, "gallery/album.html", {"album": album})


@require_GET
def image_file(request: HttpRequest, pk, variant: str) -> HttpResponse:
    """Serve a published image through the application (no public storage URL)."""
    image = selectors.public_image(pk)
    if image is None:
        raise Http404
    field = image.thumbnail if variant == "nahled" else image.image
    try:
        handle = field.open("rb")
    except FileNotFoundError:
        raise Http404 from None
    response = FileResponse(handle, content_type="image/jpeg")
    response["Cache-Control"] = "public, max-age=3600"
    response["Content-Disposition"] = "inline"
    return response
