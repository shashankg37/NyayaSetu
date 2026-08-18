"""Provider-agnostic LLM interface for NyayaSetu.

Supports HuggingFace Inference API (Qwen), Google Gemini (fallback),
and a local stub provider.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Protocol

import requests

from app.ai.ai_stubs.common import safe_json_loads
from app.ai.config import SETTINGS

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    """Protocol for LLM providers."""

    def generate(self, prompt: str, **kwargs: Any) -> str | None:
        """Generate plain text from a prompt."""
        ...

    def generate_json(self, prompt: str, **kwargs: Any) -> dict[str, Any] | None:
        """Generate structured JSON from a prompt."""
        ...


class HuggingFaceProvider:
    """HuggingFace Inference API provider (primary route for Qwen)."""

    def generate(self, prompt: str, **kwargs: Any) -> str | None:
        if not SETTINGS.hf_api_key:
            logger.warning("HF API key missing")
            return None
            
        url = f"{SETTINGS.hf_api_url.rstrip('/')}/{SETTINGS.llm_model}"
        headers = {"Authorization": f"Bearer {SETTINGS.hf_api_key}"}
        
        # Merge default params with kwargs
        params = {"max_new_tokens": 1000, "temperature": 0.1, "return_full_text": False}
        params.update(kwargs)
        
        payload = {
            "inputs": prompt,
            "parameters": params,
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=90)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list) and data:
                return str(data[0].get("generated_text") or "")
            if isinstance(data, dict):
                return str(data.get("generated_text") or data.get("text") or "")
            return None
        except Exception as e:
            logger.error("HuggingFace generation failed: %s", e)
            return None

    def generate_json(self, prompt: str, **kwargs: Any) -> dict[str, Any] | None:
        # Prompt engineering for JSON mode with Qwen
        json_prompt = f"{prompt}\n\nRespond ONLY with valid JSON. Do not include markdown blocks like ```json."
        text = self.generate(json_prompt, **kwargs)
        return safe_json_loads(text or "")


class GeminiProvider:
    """Google Gemini provider (optional fallback)."""

    def _get_model(self):
        try:
            import google.generativeai as genai  # type: ignore
            genai.configure(api_key=SETTINGS.gemini_api_key)
            return genai.GenerativeModel(SETTINGS.gemini_model)
        except ImportError:
            logger.error("google-generativeai not installed")
            return None
        except Exception as e:
            logger.error("Failed to initialize Gemini: %s", e)
            return None

    def generate(self, prompt: str, **kwargs: Any) -> str | None:
        if not SETTINGS.gemini_api_key:
            logger.warning("Gemini API key missing")
            return None
            
        model = self._get_model()
        if not model:
            return None
            
        try:
            # Handle temperature
            temp = kwargs.get("temperature", 0.1)
            config = {"temperature": temp}
            
            response = model.generate_content(prompt, generation_config=config)
            return getattr(response, "text", "") or ""
        except Exception as e:
            logger.error("Gemini generation failed: %s", e)
            return None

    def generate_json(self, prompt: str, **kwargs: Any) -> dict[str, Any] | None:
        if not SETTINGS.gemini_api_key:
            return None
            
        model = self._get_model()
        if not model:
            return None
            
        try:
            temp = kwargs.get("temperature", 0.1)
            config = {"temperature": temp, "response_mime_type": "application/json"}
            
            response = model.generate_content(prompt, generation_config=config)
            text = getattr(response, "text", "") or ""
            return safe_json_loads(text)
        except Exception as e:
            logger.error("Gemini JSON generation failed: %s", e)
            return None


class LocalProvider:
    """Local inference provider (stub for future Ollama/vLLM integration)."""

    def generate(self, prompt: str, **kwargs: Any) -> str | None:
        logger.warning("Local provider not fully implemented. Returning mock response.")
        return "This is a mock response from the local provider."

    def generate_json(self, prompt: str, **kwargs: Any) -> dict[str, Any] | None:
        logger.warning("Local provider not fully implemented. Returning mock JSON.")
        return {"mock": True, "message": "Local provider not implemented"}


# Singleton instances
_PROVIDERS: dict[str, LLMProvider] = {
    "hf": HuggingFaceProvider(),
    "gemini": GeminiProvider(),
    "local": LocalProvider(),
}


def get_provider(name: str | None = None) -> LLMProvider:
    """Get the configured or requested LLM provider."""
    provider_name = name or SETTINGS.llm_provider
    provider = _PROVIDERS.get(provider_name)
    if not provider:
        logger.warning("Provider '%s' not found, falling back to 'hf'", provider_name)
        return _PROVIDERS["hf"]
    return provider


# Legacy wrappers for backward compatibility with ai_stubs during transition
def generate_json(prompt: str) -> dict[str, Any] | None:
    """Legacy wrapper for JSON generation."""
    provider = get_provider()
    
    # Try primary provider
    result = provider.generate_json(prompt)
    if result is not None:
        return result
        
    # Try fallbacks
    fallbacks = ["gemini", "hf"]
    for fb in fallbacks:
        if fb != SETTINGS.llm_provider and _PROVIDERS[fb]:
            logger.info("Primary provider failed, trying fallback: %s", fb)
            result = _PROVIDERS[fb].generate_json(prompt)
            if result is not None:
                return result
                
    return None
