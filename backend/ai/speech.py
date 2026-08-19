"""Bhashini Speech-to-Text integration."""
from __future__ import annotations

import base64
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
    if not SETTINGS.bhashini_api_url or not SETTINGS.bhashini_api_key:
        raise SpeechTranscriptionError("Bhashini STT is not configured.")

    language = source_language or SETTINGS.bhashini_target_lang or "en"
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
                "taskType": "asr",
                "config": {
                    "language": {"sourceLanguage": language},
                    "serviceId": SETTINGS.bhashini_stt_service_id,
                    "audioFormat": "wav",
                    "samplingRate": 16000,
                },
            }
        ],
        "inputData": {"audio": [{"audioContent": base64.b64encode(audio_bytes).decode("ascii")}]},
    }
    try:
        response = requests.post(
            SETTINGS.bhashini_api_url,
            headers=headers,
            json=payload,
            timeout=SETTINGS.bhashini_timeout_seconds,
        )
    except requests.Timeout as exc:
        raise SpeechTranscriptionError("Bhashini STT timed out.") from exc
    except requests.RequestException as exc:
        raise SpeechTranscriptionError(f"Bhashini STT request failed: {exc}") from exc

    if response.status_code >= 400:
        raise SpeechTranscriptionError(f"Bhashini STT API failure ({response.status_code}).")
    try:
        data = response.json()
    except ValueError as exc:
        raise SpeechTranscriptionError("Bhashini STT returned a malformed response.") from exc

    pipeline = data.get("pipelineResponse") or data.get("output") or []
    if isinstance(pipeline, list) and pipeline:
        output = pipeline[0].get("output") or pipeline[0].get("nBestOutputs") or []
        if output:
            text = output[0].get("source") or output[0].get("target") or output[0].get("text")
            if text:
                return str(text).strip()
    text = data.get("text") or data.get("transcript")
    if text:
        return str(text).strip()
    raise SpeechTranscriptionError("Bhashini STT did not return a transcript.")
