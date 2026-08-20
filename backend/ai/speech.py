"""Sarvam Speech-to-Text and Text-to-Speech integration."""

from __future__ import annotations

import base64
from io import BytesIO
import logging

import requests

from backend.config import SETTINGS

logger = logging.getLogger(__name__)


class SpeechTranscriptionError(RuntimeError):
    """Raised when Sarvam STT fails."""


class SpeechSynthesisError(RuntimeError):
    """Raised when Sarvam TTS fails."""


def transcribe(
    audio_bytes: bytes,
    source_language: str | None = None,
) -> str:
    """Transcribe audio using Sarvam Saaras STT."""

    if not audio_bytes:
        raise SpeechTranscriptionError("Invalid audio: empty payload.")

    if len(audio_bytes) < 64:
        raise SpeechTranscriptionError(
            "Invalid audio: file is too small to transcribe."
        )

    if not SETTINGS.sarvam_api_key:
        raise SpeechTranscriptionError("Sarvam STT is not configured.")

    language = (
        source_language
        or SETTINGS.sarvam_default_language
        or "unknown"
    )

    headers = {
        "api-subscription-key": SETTINGS.sarvam_api_key,
    }

    files = {
        "file": (
            "audio.wav",
            BytesIO(audio_bytes),
            "audio/wav",
        )
    }

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
        raise SpeechTranscriptionError(
            "Sarvam STT timed out."
        ) from exc
    except requests.RequestException as exc:
        raise SpeechTranscriptionError(
            f"Sarvam STT request failed: {exc}"
        ) from exc

    if response.status_code >= 400:
        raise SpeechTranscriptionError(
            f"Sarvam STT API failure ({response.status_code})."
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise SpeechTranscriptionError(
            "Sarvam STT returned a malformed response."
        ) from exc

    text = data.get("text") or data.get("transcript")

    if text:
        return str(text).strip()

    raise SpeechTranscriptionError(
        "Sarvam STT did not return a transcript."
    )


def synthesize(
    text: str,
    target_language: str | None = None,
) -> bytes:
    """
    Convert text to speech using Sarvam Bulbul.

    Returns decoded WAV audio bytes.
    """

    if not text or not text.strip():
        raise SpeechSynthesisError(
            "Invalid TTS input: text is empty."
        )

    if not SETTINGS.sarvam_api_key:
        raise SpeechSynthesisError(
            "Sarvam TTS is not configured."
        )

    # Bulbul v3 REST API supports up to 2500 characters per request.
    text = text.strip()

    if len(text) > 2500:
        raise SpeechSynthesisError(
            "Text is too long for Sarvam Bulbul v3 TTS. "
            "Maximum is 2500 characters per request."
        )

    language = (
        target_language
        or SETTINGS.sarvam_default_language
        or "en-IN"
    )

    model = getattr(
        SETTINGS,
        "sarvam_tts_model",
        "bulbul:v3",
    )

    speaker = getattr(
        SETTINGS,
        "sarvam_tts_speaker",
        "shubh",
    )

    headers = {
        "api-subscription-key": SETTINGS.sarvam_api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "text": text,
        "model": model,
        "language_code": language,
        "speaker": speaker,
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
        raise SpeechSynthesisError(
            "Sarvam TTS timed out."
        ) from exc
    except requests.RequestException as exc:
        raise SpeechSynthesisError(
            f"Sarvam TTS request failed: {exc}"
        ) from exc

    if response.status_code >= 400:
        # Try to extract a useful error without exposing credentials.
        try:
            error_data = response.json()

            error_message = (
                error_data.get("message")
                or error_data.get("error")
                or error_data.get("detail")
                or "Unknown Sarvam error"
            )

            raise SpeechSynthesisError(
                f"Sarvam TTS API failure "
                f"({response.status_code}): {error_message}"
            )
        except ValueError:
            raise SpeechSynthesisError(
                f"Sarvam TTS API failure "
                f"({response.status_code})."
            )

    try:
        data = response.json()
    except ValueError as exc:
        raise SpeechSynthesisError(
            "Sarvam TTS returned a malformed JSON response."
        ) from exc

    audios = data.get("audios")

    if not audios or not isinstance(audios, list):
        raise SpeechSynthesisError(
            "Sarvam TTS returned no audio data."
        )

    encoded_audio = audios[0]

    if not encoded_audio:
        raise SpeechSynthesisError(
            "Sarvam TTS returned an empty audio payload."
        )

    try:
        audio_bytes = base64.b64decode(encoded_audio)
    except Exception as exc:
        raise SpeechSynthesisError(
            "Failed to decode Sarvam TTS audio."
        ) from exc

    if not audio_bytes:
        raise SpeechSynthesisError(
            "Sarvam TTS returned empty decoded audio."
        )

    return audio_bytes