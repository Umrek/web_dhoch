"""Safe image processing: validate, decode, strip metadata, resize, re-encode."""

import io
from dataclasses import dataclass

from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
THUMBNAIL_SIZE = 480
JPEG_QUALITY = 85


@dataclass(frozen=True)
class ProcessedImage:
    full: bytes
    thumbnail: bytes
    width: int
    height: int


def _encode(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    # Re-encoding from pixel data drops EXIF, GPS, ICC and any embedded payloads.
    image.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    return buffer.getvalue()


def process_image(upload) -> ProcessedImage:
    if upload.size > settings.MAX_IMAGE_BYTES:
        limit_mb = settings.MAX_IMAGE_BYTES // (1024 * 1024)
        raise ValidationError(f"Soubor je příliš velký (maximum {limit_mb} MB).")
    Image.MAX_IMAGE_PIXELS = settings.MAX_IMAGE_PIXELS
    try:
        upload.seek(0)
        with Image.open(upload) as probe:
            if probe.format not in ALLOWED_FORMATS:
                raise ValidationError("Povolené formáty jsou JPEG, PNG a WebP.")
            probe.verify()
        upload.seek(0)
        with Image.open(upload) as decoded:
            image = ImageOps.exif_transpose(decoded)
            image.load()
            has_alpha = image.mode in {"RGBA", "LA"} or "transparency" in image.info
            if has_alpha:
                rgba = image.convert("RGBA")
                flat = Image.new("RGB", rgba.size, (255, 255, 255))
                flat.paste(rgba, mask=rgba.getchannel("A"))
                image = flat
            else:
                image = image.convert("RGB")
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError) as exc:
        raise ValidationError("Soubor není platný obrázek.") from exc

    image.thumbnail((settings.IMAGE_MAX_DIMENSION, settings.IMAGE_MAX_DIMENSION))
    full = _encode(image)
    width, height = image.size
    thumb = image.copy()
    thumb.thumbnail((THUMBNAIL_SIZE, THUMBNAIL_SIZE))
    return ProcessedImage(full=full, thumbnail=_encode(thumb), width=width, height=height)
