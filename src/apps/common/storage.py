"""Private file storage. Files have no public URL; views must authorize delivery."""

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateFileSystemStorage(FileSystemStorage):
    def url(self, name: str | None) -> str:
        raise ValueError("Private files are not addressable by a public URL.")


def gallery_storage() -> PrivateFileSystemStorage:
    return PrivateFileSystemStorage(
        location=str(settings.GALLERY_ROOT),
        file_permissions_mode=0o640,
        directory_permissions_mode=0o750,
    )


def sheet_music_storage() -> PrivateFileSystemStorage:
    return PrivateFileSystemStorage(
        location=str(settings.SHEET_MUSIC_ROOT),
        file_permissions_mode=0o640,
        directory_permissions_mode=0o750,
    )
