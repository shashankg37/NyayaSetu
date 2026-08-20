"""Sarvam Bulbul v3 Text-to-Speech integration."""
from __future__ import annotations

import base64
import logging

import requests

from backend.config import SETTINGS

logger = logging.getLogger(__name__)


class SpeechSynthesisError(RuntimeError):
    pass


LANGUAGE_ALIASES = {
    "en": "en-IN",
    "hi": "hi-IN",
    "kn": "kn-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "bn": "bn-IN",
    "gu": "gu-IN",
    "ml": "ml-IN",
    "mr": "mr-IN",
    "pa": "pa-IN",
    "od": "od-IN",
}


def normalize_language_code(language: str | None) -> str:
    if not language:
        return SETTINGS.sarvam_default_language
    normalized = language.strip()
    if not normalized:
        return SETTINGS.sarvam_default_language
    if "-" in normalized:
        return normalized
    return LANGUAGE_ALIASES.get(normalized.lower(), SETTINGS.sarvam_default_language)


def synthesize(text: str, target_language: str | None = None) -> bytes:
    if not text or not text.strip():
        raise SpeechSynthesisError("No text available for speech synthesis.")
    if not SETTINGS.sarvam_api_key:
        raise SpeechSynthesisError("Sarvam TTS is not configured.")

    language = normalize_language_code(target_language)
    headers = {"api-subscription-key": SETTINGS.sarvam_api_key, "Content-Type": "application/json"}
    payload = {
        "text": text[:2500],
        "language_code": language,
        "speaker": SETTINGS.sarvam_tts_speaker,
        "model": SETTINGS.sarvam_tts_model,
        "output_audio_codec": "wav",
    }
    try:
        response = requests.post(
            f"{SETTINGS.sarvam_base_url.rstrip('/')}/text-to-speech",
            headers=headers,
            json=payload,
            timeout=SETTINGS.sarvam_timeout_seconds,
        )
    except requests.Timeout as exc:
        raise SpeechSynthesisError("Sarvam TTS timed out.") from exc
    except requests.RequestException as exc:
        raise SpeechSynthesisError(f"Sarvam TTS request failed: {exc}") from exc

    if response.status_code >= 400:
        raise SpeechSynthesisError(f"Sarvam TTS API failure ({response.status_code}).")
    try:
        data = response.json()
    except ValueError as exc:
        raise SpeechSynthesisError("Sarvam TTS returned a malformed response.") from exc

    audios = data.get("audios") or []
    encoded = audios[0] if audios else data.get("audioContent")
    if encoded:
        return base64.b64decode(encoded)
    raise SpeechSynthesisError("Sarvam TTS did not return audio.")
