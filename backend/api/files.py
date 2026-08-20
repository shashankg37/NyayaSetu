"""Upload validation helpers for user documents and audio."""
from __future__ import annotations

import re
from pathlib import Path

from fastapi import HTTPException, UploadFile

from backend.config import get_settings

ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".m4a", ".webm"}
ALLOWED_DOCUMENT_MIME = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "application/octet-stream",
}
ALLOWED_AUDIO_MIME = {
    "audio/wav",
    "audio/wave",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/ogg",
    "audio/mp4",
    "audio/x-m4a",
    "audio/webm",
    "audio/webm;codecs=opus",
    "application/octet-stream",
}
MAGIC = {
    ".pdf": b"%PDF",
    ".png": b"\x89PNG",
    ".jpg": b"\xff\xd8",
    ".jpeg": b"\xff\xd8",
}

SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def safe_filename(name: str) -> str:
    cleaned = SAFE_NAME.sub("_", Path(name).name)
    if not cleaned or cleaned in {".", ".."}:
        raise HTTPException(400, "Filename is invalid")
    return cleaned[:180]


def read_and_validate_upload(file: UploadFile, kind: str = "document") -> tuple[str, bytes, str]:
    settings = get_settings()
    if not file.filename:
        raise HTTPException(400, "Filename is required")
    filename = safe_filename(file.filename)
    suffix = Path(filename).suffix.lower()
    allowed = ALLOWED_DOCUMENT_EXTENSIONS if kind == "document" else ALLOWED_AUDIO_EXTENSIONS
    if suffix not in allowed:
        raise HTTPException(400, f"Unsupported file type: {suffix}")
    content_type = (file.content_type or "").lower()
    if kind == "document" and content_type and content_type not in ALLOWED_DOCUMENT_MIME:
        raise HTTPException(400, f"Unsupported MIME type: {content_type}")
    if kind == "audio" and content_type and content_type not in ALLOWED_AUDIO_MIME:
        raise HTTPException(400, f"Unsupported MIME type: {content_type}")
    data = file.file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(413, "Upload exceeds the configured size limit")
    magic = MAGIC.get(suffix)
    if magic and not data.startswith(magic) and suffix != ".webp":
        raise HTTPException(400, "File content does not match the declared type")
    return filename, data, content_type
