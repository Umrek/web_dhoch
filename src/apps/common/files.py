"""Filename and hashing helpers for uploaded files."""

import hashlib
import os
import re
import unicodedata
from typing import BinaryIO


def safe_stem(name: str, *, default: str = "soubor", max_length: int = 60) -> str:
    """Return an ASCII-only, path-free filename stem (no extension)."""
    base = os.path.basename(name.replace("\\", "/"))
    stem, _ = os.path.splitext(base)
    ascii_stem = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "-", ascii_stem).strip("-_")
    return cleaned[:max_length] or default


def extension_of(name: str) -> str:
    return os.path.splitext(os.path.basename(name.replace("\\", "/")))[1].lower()


def sha256_hexdigest(fileobj: BinaryIO) -> str:
    digest = hashlib.sha256()
    fileobj.seek(0)
    for chunk in iter(lambda: fileobj.read(1024 * 1024), b""):
        digest.update(chunk)
    fileobj.seek(0)
    return digest.hexdigest()
