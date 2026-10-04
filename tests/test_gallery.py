"""Gallery: safe image processing, metadata stripping, publication-gated delivery."""

import io

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from apps.gallery.images import process_image
from apps.gallery.models import Album, GalleryImage
from apps.gallery.services import delete_album, delete_image, store_image

from .conftest import make_image_bytes

pytestmark = pytest.mark.django_db


def upload(data: bytes, name="foto.jpg") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, data, content_type="image/jpeg")


def jpeg_with_exif(orientation=1) -> bytes:
    image = Image.new("RGB", (40, 20), (200, 10, 10))
    exif = Image.Exif()
    exif[0x010F] = "TajnaZnackaFotoaparatu"
    exif[0x0112] = orientation
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", exif=exif.tobytes())
    return buffer.getvalue()


@pytest.fixture
def album():
    return Album.objects.create(title="Hody", slug="hody", is_published=True)


def add_image(album, **kwargs):
    image = GalleryImage(album=album, alt_text="Kapela hraje", **kwargs)
    return store_image(image, process_image(upload(make_image_bytes())), actor=None)


def test_exif_metadata_is_stripped():
    out = process_image(upload(jpeg_with_exif()))
    assert b"TajnaZnackaFotoaparatu" not in out.full
    assert len(Image.open(io.BytesIO(out.full)).getexif()) == 0


def test_orientation_is_applied_before_stripping():
    out = process_image(upload(jpeg_with_exif(orientation=6)))
    assert (out.width, out.height) == (20, 40)


def test_large_images_are_downscaled_and_thumbnail_made(settings):
    settings.IMAGE_MAX_DIMENSION = 100
    out = process_image(upload(make_image_bytes((400, 200))))
    assert max(out.width, out.height) == 100
    assert max(Image.open(io.BytesIO(out.thumbnail)).size) <= 100


@pytest.mark.parametrize(
    "data",
    [b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>", b"GIF89a....", b"not an image", b""],
)
def test_non_images_and_svg_are_rejected(data):
    with pytest.raises(ValidationError):
        process_image(upload(data))


def test_gif_format_is_rejected():
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4)).save(buffer, format="GIF")
    with pytest.raises(ValidationError):
        process_image(upload(buffer.getvalue(), "a.jpg"))


def test_oversized_file_rejected(settings):
    settings.MAX_IMAGE_BYTES = 10
    with pytest.raises(ValidationError):
        process_image(upload(make_image_bytes()))


def test_decompression_bomb_guard(settings):
    settings.MAX_IMAGE_PIXELS = 100
    with pytest.raises(ValidationError):
        process_image(upload(make_image_bytes((400, 400))))


def test_png_with_transparency_is_flattened():
    buffer = io.BytesIO()
    Image.new("RGBA", (10, 10), (0, 0, 0, 0)).save(buffer, format="PNG")
    out = process_image(upload(buffer.getvalue(), "a.png"))
    assert Image.open(io.BytesIO(out.full)).mode == "RGB"


def test_published_image_is_served_through_app(client, album):
    image = add_image(album)
    response = client.get(reverse("gallery:image", args=[image.pk, "nahled"]))
    assert response.status_code == 200
    assert response["Content-Type"] == "image/jpeg"
    assert b"".join(response.streaming_content)[:2] == b"\xff\xd8"


def test_unpublished_image_or_album_is_not_served(client, album):
    hidden_image = add_image(album, is_published=False)
    assert client.get(reverse("gallery:image", args=[hidden_image.pk, "plny"])).status_code == 404
    visible = add_image(album)
    album.is_published = False
    album.save()
    assert client.get(reverse("gallery:image", args=[visible.pk, "plny"])).status_code == 404
    assert client.get(reverse("gallery:album", args=[album.slug])).status_code == 404


def test_unknown_variant_is_404(client, album):
    image = add_image(album)
    assert client.get(f"/galerie/foto/{image.pk}/original/").status_code == 404


def test_images_have_no_public_storage_url(album):
    image = add_image(album)
    with pytest.raises(ValueError, match="public URL"):
        image.image.url  # noqa: B018


def test_album_page_uses_alt_text(client, album):
    add_image(album)
    html = client.get(reverse("gallery:album", args=[album.slug])).content.decode()
    assert 'alt="Kapela hraje"' in html


def test_empty_album_not_listed(client, album):
    assert "Hody" not in client.get(reverse("gallery:list")).content.decode()


def test_delete_image_and_album_remove_files(album, musician):
    image = add_image(album)
    path = image.image.path
    delete_image(image, actor=musician)
    import os

    assert not os.path.exists(path)
    other = add_image(album)
    other_path = other.thumbnail.path
    delete_album(album, actor=musician)
    assert not os.path.exists(other_path)
    assert not GalleryImage.objects.exists()
