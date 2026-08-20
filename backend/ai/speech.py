"""Sarvam Saaras v3 Speech-to-Text integration."""
from __future__ import annotations

from io import BytesIO
import logging

import requests

from backend.config import SETTINGS

logger = logging.getLogger(__name__)


class SpeechTranscriptionError(RuntimeError):
    pass


def transcribe(audio_bytes: bytes, source_language: str | None = None) -> str:
    if not audio_bytes:
        raise SpeechTranscriptionError("Invalid audio: empty payload.")
    if len(audio_bytes) < 64:
        raise SpeechTranscriptionError("Invalid audio: file is too small to transcribe.")
    if not SETTINGS.sarvam_api_key:
        raise SpeechTranscriptionError("Sarvam STT is not configured.")

    language = source_language or SETTINGS.sarvam_default_language or "unknown"
    headers = {"api-subscription-key": SETTINGS.sarvam_api_key}
    files = {"file": ("audio.wav", BytesIO(audio_bytes), "audio/wav")}
    data = {
        "model": SETTINGS.sarvam_stt_model,
        "mode": "transcribe",
        "language_code": language,
    }
    try:
        response = requests.post(
            f"{SETTINGS.sarvam_base_url.rstrip('/')}/speech-to-text",
            headers=headers,
            files=files,
            data=data,
            timeout=SETTINGS.sarvam_timeout_seconds,
        )
    except requests.Timeout as exc:
        raise SpeechTranscriptionError("Sarvam STT timed out.") from exc
    except requests.RequestException as exc:
        raise SpeechTranscriptionError(f"Sarvam STT request failed: {exc}") from exc

    if response.status_code >= 400:
        raise SpeechTranscriptionError(f"Sarvam STT API failure ({response.status_code}).")
    try:
        data = response.json()
    except ValueError as exc:
        raise SpeechTranscriptionError("Sarvam STT returned a malformed response.") from exc

    text = data.get("text") or data.get("transcript")
    if text:
        return str(text).strip()
    raise SpeechTranscriptionError("Sarvam STT did not return a transcript.")
