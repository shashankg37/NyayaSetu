"""Speech-to-Text (STT) module using Bhashini ULCA API."""
from __future__ import annotations

import base64
import logging
import os
import requests

from app.ai.config import SETTINGS
from app.ai.langid import detect_language

logger = logging.getLogger(__name__)


def _bhashini_transcribe(audio_bytes: bytes, source_language: str = "en") -> str | None:
    """Transcribe audio using Bhashini's ULCA pipeline."""
    # We require three env vars for proper ULCA flow
    user_id = os.getenv("BHASHINI_USER_ID")
    api_key = os.getenv("BHASHINI_ULCA_API_KEY")
    pipeline_url = os.getenv("BHASHINI_PIPELINE_URL", "https://dhruva-api.bhashini.gov.in/services/inference/pipeline")

    if not user_id or not api_key:
        logger.warning("Bhashini ULCA credentials not configured")
        return None

    # Step 1: Request pipeline configuration to get the service ID for ASR
    headers = {
        "userID": user_id,
        "ulcaApiKey": api_key,
        "Content-Type": "application/json",
    }
    
    config_payload = {
        "pipelineTasks": [
            {
                "taskType": "asr",
                "config": {"language": {"sourceLanguage": source_language}}
            }
        ],
        "pipelineRequestConfig": {"pipelineId": "64392f96daac500b55c543cd"} # Standard Bhashini pipeline ID
    }

    try:
        config_res = requests.post(pipeline_url, headers=headers, json=config_payload, timeout=10)
        config_res.raise_for_status()
        config_data = config_res.json()
        
        # Extract the service ID for ASR
        service_id = ""
        for task in config_data.get("pipelineResponseConfig", []):
            if task.get("taskType") == "asr":
                service_id = task.get("config", [{}])[0].get("serviceId", "")
                break
                
        if not service_id:
            logger.error("Could not find ASR service ID in Bhashini config response")
            return None
            
        # Step 2: Make the actual compute request
        compute_payload = {
            "pipelineTasks": [
                {
                    "taskType": "asr",
                    "config": {
                        "language": {"sourceLanguage": source_language},
                        "serviceId": service_id,
                        "audioFormat": "wav",
                        "samplingRate": 16000
                    }
                }
            ],
            "inputData": {
                "audio": [
                    {
                        "audioContent": base64.b64encode(audio_bytes).decode("ascii")
                    }
                ]
            }
        }
        
        # The compute endpoint is typically the same URL or derived from it
        compute_url = pipeline_url.replace("/pipeline", "")
        
        # The compute headers require the inference API key returned from the config step
        # (This varies by Bhashini version, but usually requires Authorization)
        inference_api_key = config_data.get("pipelineInferenceAPIEndPoint", {}).get("inferenceApiKey", {}).get("value")
        
        if inference_api_key:
            headers["Authorization"] = inference_api_key
            
        compute_res = requests.post(compute_url, headers=headers, json=compute_payload, timeout=90)
        compute_res.raise_for_status()
        compute_data = compute_res.json()
        
        # Extract transcript
        for output in compute_data.get("pipelineResponse", []):
            if output.get("taskType") == "asr":
                return output.get("output", [{}])[0].get("source", "")
                
    except Exception as e:
        logger.error("Bhashini ASR failed: %s", e)
        return None
        
    return None


def _local_whisper_fallback(audio_bytes: bytes) -> str | None:
    """Fallback to local Whisper model if Bhashini fails or isn't configured."""
    try:
        import tempfile
        import whisper  # type: ignore

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
            handle.write(audio_bytes)
            temp_path = handle.name
            
        try:
            # Note: base model is 74M params. Might want to use 'tiny' for speed in production
            model = whisper.load_model("base")
            result = model.transcribe(temp_path)
            return (result.get("text") or "").strip()
        finally:
            from pathlib import Path
            Path(temp_path).unlink(missing_ok=True)
    except ImportError:
        logger.warning("Whisper not installed for fallback STT")
        return None
    except Exception as e:
        logger.error("Whisper fallback failed: %s", e)
        return None


def transcribe(audio_bytes: bytes) -> str:
    """Transcribe audio to text, using Bhashini with Whisper fallback.
    
    If BHASHINI_MOCK_TRANSCRIPT is set, returns that directly for testing.
    """
    mock_transcript = os.getenv("BHASHINI_MOCK_TRANSCRIPT", "").strip()
    if mock_transcript:
        logger.info("Using mock transcript: %s", mock_transcript)
        return mock_transcript
        
    transcript = _bhashini_transcribe(audio_bytes)
    
    if not transcript:
        logger.info("Bhashini ASR failed, trying Whisper fallback")
        transcript = _local_whisper_fallback(audio_bytes)
        
    if not transcript:
        logger.warning("All ASR methods failed")
        return ""
        
    return transcript
