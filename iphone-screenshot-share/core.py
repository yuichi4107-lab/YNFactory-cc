from __future__ import annotations

import os
from datetime import datetime


def is_allowed(chat_id, allowlist):
    """True only if allowlist is non-empty AND chat_id is in it.

    An empty allowlist means 'setup mode': nothing is accepted yet.
    """
    return bool(allowlist) and chat_id in allowlist


MIME_EXT = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "image/heif": ".heif",
}


def _ext_from_document(doc):
    name = doc.get("file_name") or ""
    _, ext = os.path.splitext(name)
    if ext:
        return ext.lower()
    mime = (doc.get("mime_type") or "").lower()
    return MIME_EXT.get(mime, ".bin")


def extract_image(message):
    """Return (file_id, ext) for the best image in a message, or None.

    - 'photo': list of PhotoSize; pick the largest by width*height (ext '.jpg').
    - 'document' with image/* mime: use it (ext from file_name or mime).
    Anything else returns None.
    """
    if not isinstance(message, dict):
        return None
    photos = message.get("photo")
    if photos:
        best = max(photos, key=lambda p: p.get("width", 0) * p.get("height", 0))
        return (best["file_id"], ".jpg")
    doc = message.get("document")
    if doc:
        mime = (doc.get("mime_type") or "").lower()
        if mime.startswith("image/"):
            return (doc["file_id"], _ext_from_document(doc))
    return None
