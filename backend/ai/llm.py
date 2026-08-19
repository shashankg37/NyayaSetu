"""Provider-agnostic LLM interface for NyayaSetu.

Supports HuggingFace Inference API (Qwen), Google Gemini (fallback),
and a local stub provider.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Protocol

import requests

from backend.config import SETTINGS

logger = logging.getLogger(__name__)


def safe_json_loads(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    candidates = [text]
    if "```" in text:
        candidates.extend(segment for segment in text.split("```") if segment.strip())
    for candidate in candidates:
        candidate = candidate.strip()
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(candidate[start : end + 1])
            except json.JSONDecodeError:
                continue
    return None


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


def generate_json_from_any(prompt: str) -> dict[str, Any] | None:
    """Generate JSON using primary or fallback providers."""
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


# --- Answer Generation Logic ---

def _fallback_response(query: str, chunks: list[dict[str, Any]], confidence: float) -> dict[str, Any]:
    return {
        "your_right": "I could not find a strong enough legal match in the grounded corpus to answer confidently.",
        "what_law_says": "This case needs human review. Please contact your nearest District Legal Services Authority or the NALSA helpline for guided assistance.",
        "what_this_means": "The system is not making a legal claim here because the retrieved evidence is too weak.",
        "what_you_can_do": [
            "Visit or call your local District Legal Services Authority.",
            "Keep any letters, payslips, notices, or messages that support your case.",
            "If this is urgent, ask a lawyer or legal aid clinic to review the facts directly.",
        ],
        "source": {"act": "NALSA / DLSA routing", "section": "Legal aid support"},
        "confidence": float(confidence),
        "fallback_used": True,
        "query": query,
        "next_action": "legal_aid_or_more_information",
    }


def _synthesize_from_chunks(query: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
    top = chunks[0]
    act = top.get("act", "Unknown act")
    section = top.get("section", "Unknown section")
    simplified = top.get("simplified_text") or top.get("original_text") or ""
    return {
        "your_right": f"The strongest grounded match points to {act}, {section}.",
        "what_law_says": simplified or "The retrieved chunk describes the relevant legal rule.",
        "what_this_means": "Based on the retrieved material, the issue appears to fall under the cited provision.",
        "what_you_can_do": [
            "Review the cited source in full before taking action.",
            "Keep supporting documents ready in case you need legal aid or a claim filing.",
        ],
        "source": {"act": act, "section": section},
        "confidence": float(top.get("confidence", 0.0)),
        "fallback_used": False,
        "query": query,
        "next_action": "review_cited_source",
    }


def _build_context(chunks: list[dict[str, Any]]) -> str:
    lines = []
    for idx, chunk in enumerate(chunks[:5], start=1):
        lines.append(
            f"{idx}. Act: {chunk.get('act', '')}\nSection: {chunk.get('section', '')}\nTopic: {chunk.get('topic', '')}\nText: {chunk.get('simplified_text') or chunk.get('original_text') or ''}"
        )
    return "\n\n".join(lines)


def _provider_generate(query: str, chunks: list[dict[str, Any]]) -> dict[str, Any] | None:
    prompt = (
        "You are Nyaya Setu, an Indian legal-awareness assistant. Use only the supplied chunks. "
        "Do not invent law. Cite one act and section from the evidence. Return JSON only with keys: "
        "your_right, what_law_says, what_this_means, what_you_can_do, source, confidence, fallback_used.\n\n"
        f"Question:\n{query}\n\nGrounded chunks:\n{_build_context(chunks)}"
    )
    return generate_json_from_any(prompt)


def generate_answer(query: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
    if not chunks:
        return _fallback_response(query, chunks, 0.0)
    top_confidence = float(chunks[0].get("confidence", 0.0))
    if top_confidence < SETTINGS.confidence_threshold:
        return _fallback_response(query, chunks, top_confidence)
    provider_answer = _provider_generate(query, chunks)
    if provider_answer:
        provider_answer.setdefault("confidence", top_confidence)
        provider_answer.setdefault("fallback_used", False)
        source = provider_answer.get("source")
        if isinstance(source, list):
            provider_answer["source"] = source[0] if source else {}
        provider_answer.setdefault("source", {"act": chunks[0].get("act", "Unknown act"), "section": chunks[0].get("section", "")})
        provider_answer.setdefault("query", query)
        return provider_answer
    return _synthesize_from_chunks(query, chunks)
