from __future__ import annotations

from typing import Any
import json

import requests

from app.ai.ai_stubs.common import safe_json_loads
from app.ai.config import SETTINGS


def _hf_generate(prompt: str) -> str | None:
    if not SETTINGS.hf_api_key:
        return None
    url = f"{SETTINGS.hf_api_url.rstrip('/')}/{SETTINGS.llm_model}"
    headers = {"Authorization": f"Bearer {SETTINGS.hf_api_key}"}
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 700, "temperature": 0.1, "return_full_text": False},
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and data:
            return str(data[0].get("generated_text") or "")
        if isinstance(data, dict):
            return str(data.get("generated_text") or data.get("text") or "")
    except Exception:
        return None
    return None


def _gemini_generate(prompt: str) -> str | None:
    if not SETTINGS.gemini_api_key:
        return None
    try:
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=SETTINGS.gemini_api_key)
        model = genai.GenerativeModel(SETTINGS.gemini_model)
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return getattr(response, "text", "") or ""
    except Exception:
        return None


def generate_json(prompt: str) -> dict[str, Any] | None:
    """Generate JSON through the configured provider, returning None when unavailable."""
    provider_order = [SETTINGS.llm_provider]
    if SETTINGS.llm_provider != "gemini":
        provider_order.append("gemini")
    if SETTINGS.llm_provider != "hf":
        provider_order.append("hf")

    for provider in provider_order:
        text = _hf_generate(prompt) if provider == "hf" else _gemini_generate(prompt) if provider == "gemini" else None
        parsed = safe_json_loads(text or "")
        if parsed:
            return parsed
    return None

