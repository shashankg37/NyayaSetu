"""Text-to-Speech (TTS) module using Bhashini ULCA API."""
from __future__ import annotations

import base64
import logging
import os
import requests

logger = logging.getLogger(__name__)


def synthesize(text: str, target_language: str = "en", gender: str = "female") -> bytes | None:
    """Synthesize text to speech using Bhashini's ULCA pipeline."""
    if not text or not text.strip():
        return None

    # We require three env vars for proper ULCA flow
    user_id = os.getenv("BHASHINI_USER_ID")
    api_key = os.getenv("BHASHINI_ULCA_API_KEY")
    pipeline_url = os.getenv("BHASHINI_PIPELINE_URL", "https://dhruva-api.bhashini.gov.in/services/inference/pipeline")

    if not user_id or not api_key:
        logger.warning("Bhashini ULCA credentials not configured for TTS")
        return None

    # Step 1: Request pipeline configuration to get the service ID for TTS
    headers = {
        "userID": user_id,
        "ulcaApiKey": api_key,
        "Content-Type": "application/json",
    }
    
    config_payload = {
        "pipelineTasks": [
            {
                "taskType": "tts",
                "config": {"language": {"sourceLanguage": target_language}}
            }
        ],
        "pipelineRequestConfig": {"pipelineId": "64392f96daac500b55c543cd"}
    }

    try:
        config_res = requests.post(pipeline_url, headers=headers, json=config_payload, timeout=10)
        config_res.raise_for_status()
        config_data = config_res.json()
        
        # Extract the service ID for TTS
        service_id = ""
        for task in config_data.get("pipelineResponseConfig", []):
            if task.get("taskType") == "tts":
                service_id = task.get("config", [{}])[0].get("serviceId", "")
                break
                
        if not service_id:
            logger.error("Could not find TTS service ID in Bhashini config response")
            return None
            
        # Step 2: Make the actual compute request
        compute_payload = {
            "pipelineTasks": [
                {
                    "taskType": "tts",
                    "config": {
                        "language": {"sourceLanguage": target_language},
                        "serviceId": service_id,
                        "gender": gender,
                        "samplingRate": 16000
                    }
                }
            ],
            "inputData": {
                "input": [
                    {
                        "source": text
                    }
                ]
            }
        }
        
        compute_url = pipeline_url.replace("/pipeline", "")
        
        inference_api_key = config_data.get("pipelineInferenceAPIEndPoint", {}).get("inferenceApiKey", {}).get("value")
        
        if inference_api_key:
            headers["Authorization"] = inference_api_key
            
        compute_res = requests.post(compute_url, headers=headers, json=compute_payload, timeout=90)
        compute_res.raise_for_status()
        compute_data = compute_res.json()
        
        # Extract audio bytes
        for output in compute_data.get("pipelineResponse", []):
            if output.get("taskType") == "tts":
                audio_b64 = output.get("audio", [{}])[0].get("audioContent", "")
                if audio_b64:
                    return base64.b64decode(audio_b64)
                    
    except Exception as e:
        logger.error("Bhashini TTS failed: %s", e)
        return None
        
    return None
