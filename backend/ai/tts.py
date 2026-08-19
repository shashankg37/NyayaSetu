"""Bhashini Text-to-Speech integration."""
from __future__ import annotations

import base64
import logging

import requests

from backend.config import SETTINGS

logger = logging.getLogger(__name__)


class SpeechSynthesisError(RuntimeError):
    pass


def synthesize(text: str, target_language: str | None = None) -> bytes:
    if not text or not text.strip():
        raise SpeechSynthesisError("No text available for speech synthesis.")
    if not SETTINGS.bhashini_api_url or not SETTINGS.bhashini_api_key:
        raise SpeechSynthesisError("Bhashini TTS is not configured.")

    language = target_language or SETTINGS.bhashini_target_lang or "en"
    headers = {
        "Authorization": SETTINGS.bhashini_api_key,
        "ulcaApiKey": SETTINGS.bhashini_api_key,
        "userID": SETTINGS.bhashini_user_id,
        "Content-Type": "application/json",
    }
    payload = {
        "pipelineId": SETTINGS.bhashini_pipeline_id,
        "pipelineTasks": [
            {
                "taskType": "tts",
                "config": {
                    "language": {"sourceLanguage": language},
                    "serviceId": SETTINGS.bhashini_tts_service_id,
                    "gender": "female",
                    "samplingRate": 22050,
                },
            }
        ],
        "inputData": {"input": [{"source": text[:1500]}]},
    }
    try:
        response = requests.post(
            SETTINGS.bhashini_api_url,
            headers=headers,
            json=payload,
            timeout=SETTINGS.bhashini_timeout_seconds,
        )
    except requests.Timeout as exc:
        raise SpeechSynthesisError("Bhashini TTS timed out.") from exc
    except requests.RequestException as exc:
        raise SpeechSynthesisError(f"Bhashini TTS request failed: {exc}") from exc

    if response.status_code >= 400:
        raise SpeechSynthesisError(f"Bhashini TTS API failure ({response.status_code}).")
    try:
        data = response.json()
    except ValueError as exc:
        raise SpeechSynthesisError("Bhashini TTS returned a malformed response.") from exc

    pipeline = data.get("pipelineResponse") or []
    if isinstance(pipeline, list) and pipeline:
        audio = pipeline[0].get("audio") or []
        if audio:
            encoded = audio[0].get("audioContent")
            if encoded:
                return base64.b64decode(encoded)
    encoded = data.get("audioContent")
    if encoded:
        return base64.b64decode(encoded)
    raise SpeechSynthesisError("Bhashini TTS did not return audio.")
