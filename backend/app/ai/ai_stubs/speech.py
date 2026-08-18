from __future__ import annotations

from pathlib import Path
from typing import Any
import base64
import json
import os

import requests

from app.ai.config import SETTINGS


def _detect_language(text: str) -> str:
    try:
        import fasttext  # type: ignore

        model_path = Path(SETTINGS.fasttext_langid_model)
        if model_path.exists():
            model = fasttext.load_model(str(model_path))
            labels, _ = model.predict(text.replace("\n", " "), k=1)
            if labels:
                return labels[0].replace("__label__", "")
    except Exception:
        pass
    devanagari = sum(1 for ch in text if "\u0900" <= ch <= "\u097f")
    if devanagari:
        return "hi"
    tamil = sum(1 for ch in text if "\u0b80" <= ch <= "\u0bff")
    if tamil:
        return "ta"
    return "en"


def _bhashini_transcribe(audio_bytes: bytes) -> str | None:
    if not SETTINGS.bhashini_api_url:
        return None
    headers = {"Content-Type": "application/json"}
    if SETTINGS.bhashini_api_key:
        headers["Authorization"] = f"Bearer {SETTINGS.bhashini_api_key}"
    payload = {"audio_b64": base64.b64encode(audio_bytes).decode("ascii")}
    try:
        response = requests.post(SETTINGS.bhashini_api_url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        for key in ("transcript", "text", "output"):
            if data.get(key):
                return str(data[key])
    except Exception:
        return None
    return None


def _local_whisper_fallback(audio_bytes: bytes) -> str | None:
    try:
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
            handle.write(audio_bytes)
            temp_path = handle.name
        try:
            import whisper  # type: ignore

            model = whisper.load_model("base")
            result = model.transcribe(temp_path)
            return (result.get("text") or "").strip()
        finally:
            Path(temp_path).unlink(missing_ok=True)
    except Exception:
        return None


def _translate_if_needed(text: str) -> str:
    language = _detect_language(text)
    if language == SETTINGS.working_language:
        return text
    if not SETTINGS.bhashini_translate_url:
        return text
    headers = {"Content-Type": "application/json"}
    if SETTINGS.bhashini_api_key:
        headers["Authorization"] = f"Bearer {SETTINGS.bhashini_api_key}"
    payload = {
        "text": text,
        "source_language": language,
        "target_language": SETTINGS.bhashini_target_lang,
    }
    try:
        response = requests.post(
            SETTINGS.bhashini_translate_url, headers=headers, json=payload, timeout=90
        )
        response.raise_for_status()
        data = response.json()
        return str(data.get("translated_text") or data.get("text") or text)
    except Exception:
        return text


def transcribe(audio_bytes: bytes) -> str:
    """Transcribes voice input to text, translating to a working language if needed."""
    mock_transcript = os.getenv("BHASHINI_MOCK_TRANSCRIPT", "").strip()
    if mock_transcript:
        return mock_transcript
    transcript = _bhashini_transcribe(audio_bytes)
    if not transcript:
        transcript = _local_whisper_fallback(audio_bytes)
    if not transcript:
        raise RuntimeError(
            "No speech provider is configured. Set BHASHINI_API_URL or BHASHINI_MOCK_TRANSCRIPT."
        )
    return _translate_if_needed(transcript)

