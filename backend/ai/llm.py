"""Provider-agnostic LLM interface for NyayaSetu.

Primary path: Hugging Face Inference (Qwen). Gemini remains an optional fallback.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Protocol

import requests

from backend.config import SETTINGS

logger = logging.getLogger(__name__)


class LLMUnavailableError(RuntimeError):
    """Raised when no configured inference provider can generate a response."""


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
                parsed = json.loads(candidate[start : end + 1])
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
    return None


def citations_from_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    seen: set[tuple[Any, Any, Any]] = set()
    for chunk in chunks:
        act = chunk.get("act") or chunk.get("document_name") or chunk.get("source")
        section = chunk.get("section") or None
        page = chunk.get("page")
        url = chunk.get("source_url") or None
        key = (act, section, page)
        if not act or key in seen:
            continue
        seen.add(key)
        citations.append(
            {
                "document_name": chunk.get("document_name") or act,
                "act": act,
                "section": section,
                "page": page,
                "source_url": url,
            }
        )
    return citations


class LLMProvider(Protocol):
    def generate(self, prompt: str, **kwargs: Any) -> str | None: ...
    def generate_json(self, prompt: str, **kwargs: Any) -> dict[str, Any] | None: ...


def _chat_text_from_hf(data: Any) -> str | None:
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            return str(first.get("generated_text") or first.get("text") or "") or None
    if isinstance(data, dict):
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message") or {}
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                return content
            if isinstance(content, list):
                parts = [part.get("text", "") for part in content if isinstance(part, dict)]
                joined = "".join(parts).strip()
                return joined or None
        return str(data.get("generated_text") or data.get("text") or "") or None
    return None


class HuggingFaceProvider:
    """Hugging Face Inference provider for Qwen."""

    def generate(self, prompt: str, **kwargs: Any) -> str | None:
        if not SETTINGS.hf_api_key:
            logger.warning("HF API key missing")
            return None
        max_tokens = int(kwargs.get("max_new_tokens") or kwargs.get("max_tokens") or 1000)
        temperature = float(kwargs.get("temperature", 0.1))
        try:
            from huggingface_hub import InferenceClient  # type: ignore

            client = InferenceClient(token=SETTINGS.hf_api_key)
            completion = client.chat.completions.create(
                model=SETTINGS.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            content = completion.choices[0].message.content
            return str(content) if content else None
        except Exception as hub_error:
            logger.info("HF chat client failed, trying HTTP inference: %s", hub_error)

        headers = {"Authorization": f"Bearer {SETTINGS.hf_api_key}"}
        urls = [
            f"{SETTINGS.hf_api_url.rstrip('/')}/{SETTINGS.llm_model}",
            f"https://api-inference.huggingface.co/models/{SETTINGS.llm_model}",
        ]
        payloads = [
            {
                "model": SETTINGS.llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature,
                    "return_full_text": False,
                },
            },
        ]
        for url in urls:
            for payload in payloads:
                try:
                    response = requests.post(url, headers=headers, json=payload, timeout=90)
                    if response.status_code >= 400:
                        logger.warning("HF HTTP %s for %s: %s", response.status_code, url, response.text[:300])
                        continue
                    text = _chat_text_from_hf(response.json())
                    if text:
                        return text
                except Exception as exc:
                    logger.error("HuggingFace generation failed: %s", exc)
        return None

    def generate_json(self, prompt: str, **kwargs: Any) -> dict[str, Any] | None:
        json_prompt = f"{prompt}\n\nRespond ONLY with valid JSON. Do not include markdown fences."
        text = self.generate(json_prompt, **kwargs)
        return safe_json_loads(text or "")


class GeminiProvider:
    def _get_model(self):
        try:
            import google.generativeai as genai  # type: ignore

            genai.configure(api_key=SETTINGS.gemini_api_key)
            return genai.GenerativeModel(SETTINGS.gemini_model)
        except Exception as exc:
            logger.error("Failed to initialize Gemini: %s", exc)
            return None

    def generate(self, prompt: str, **kwargs: Any) -> str | None:
        if not SETTINGS.gemini_api_key:
            return None
        model = self._get_model()
        if not model:
            return None
        try:
            response = model.generate_content(
                prompt,
                generation_config={"temperature": kwargs.get("temperature", 0.1)},
            )
            return getattr(response, "text", "") or ""
        except Exception as exc:
            logger.error("Gemini generation failed: %s", exc)
            return None

    def generate_json(self, prompt: str, **kwargs: Any) -> dict[str, Any] | None:
        if not SETTINGS.gemini_api_key:
            return None
        model = self._get_model()
        if not model:
            return None
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": kwargs.get("temperature", 0.1),
                    "response_mime_type": "application/json",
                },
            )
            return safe_json_loads(getattr(response, "text", "") or "")
        except Exception as exc:
            logger.error("Gemini JSON generation failed: %s", exc)
            return None


class LocalProvider:
    def generate(self, prompt: str, **kwargs: Any) -> str | None:
        logger.error("Local provider is not configured for Qwen inference.")
        return None

    def generate_json(self, prompt: str, **kwargs: Any) -> dict[str, Any] | None:
        return None


_PROVIDERS: dict[str, LLMProvider] = {
    "hf": HuggingFaceProvider(),
    "gemini": GeminiProvider(),
    "local": LocalProvider(),
}


def get_provider(name: str | None = None) -> LLMProvider:
    provider_name = name or SETTINGS.llm_provider
    return _PROVIDERS.get(provider_name) or _PROVIDERS["hf"]


def generate_json_from_any(prompt: str) -> dict[str, Any] | None:
    provider = get_provider()
    result = provider.generate_json(prompt)
    if result is not None:
        return result
    for fallback in ("gemini", "hf"):
        if fallback == SETTINGS.llm_provider:
            continue
        result = _PROVIDERS[fallback].generate_json(prompt)
        if result is not None:
            return result
    return None


def generate_text_from_any(prompt: str) -> str | None:
    provider = get_provider()
    result = provider.generate(prompt)
    if result:
        return result
    for fallback in ("gemini", "hf"):
        if fallback == SETTINGS.llm_provider:
            continue
        result = _PROVIDERS[fallback].generate(prompt)
        if result:
            return result
    return None


def _fallback_response(query: str, chunks: list[dict[str, Any]], reason: str, service_error: bool = False) -> dict[str, Any]:
    return {
        "your_right": "I could not find sufficient authoritative legal evidence to answer this confidently."
        if not service_error
        else "The legal answer service is currently unavailable.",
        "what_law_says": reason,
        "what_this_means": "The system is not making a legal claim because evidence or inference is insufficient.",
        "what_you_can_do": [
            "Contact your nearest District Legal Services Authority or NALSA helpline.",
            "Keep documents such as payslips, notices, or receipts.",
            "Ask a qualified lawyer or legal-aid clinic to review the facts.",
        ],
        "source": None,
        "citations": citations_from_chunks(chunks),
        "fallback_used": True,
        "service_error": service_error,
        "query": query,
        "next_action": "legal_aid_or_more_information",
        "disclaimer": "This is legal awareness information, not legal advice.",
    }


def _build_context(chunks: list[dict[str, Any]]) -> str:
    lines = []
    for idx, chunk in enumerate(chunks[:5], start=1):
        lines.append(
            "\n".join(
                [
                    f"{idx}. document_name: {chunk.get('document_name', '')}",
                    f"act/source: {chunk.get('act') or chunk.get('source', '')}",
                    f"section: {chunk.get('section', '')}",
                    f"page: {chunk.get('page', '')}",
                    f"source_url: {chunk.get('source_url', '')}",
                    f"text: {chunk.get('original_text') or chunk.get('simplified_text') or ''}",
                ]
            )
        )
    return "\n\n".join(lines)


def generate_answer(
    query: str,
    chunks: list[dict[str, Any]],
    history: list[dict[str, Any]] | None = None,
    extracted_document: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not chunks:
        return _fallback_response(query, chunks, "No official knowledge-base chunks were retrieved.")

    history_text = ""
    if history:
        recent = history[-6:]
        history_text = "\n".join(f"{item.get('role')}: {item.get('content')}" for item in recent)

    extracted = ""
    if extracted_document:
        extracted = json.dumps(extracted_document.get("extracted_fields") or {}, ensure_ascii=False)

    prompt = (
        "You are Nyaya Setu, an Indian legal-awareness assistant. Use only the supplied official chunks. "
        "Do not invent law, sections, cases, or URLs. If a fact is not in the chunks, say so. "
        "Clearly separate: (1) facts from a user document if provided, (2) official knowledge-base text, "
        "(3) your interpretation. Return JSON with keys: your_right, what_law_says, what_this_means, "
        "what_you_can_do (array), interpretation, next_action. Do not include a numeric confidence score.\n\n"
        f"Conversation:\n{history_text}\n\nQuestion:\n{query}\n\n"
        f"User document extraction (not law):\n{extracted}\n\nOfficial chunks:\n{_build_context(chunks)}"
    )
    provider_answer = generate_json_from_any(prompt)
    if not provider_answer:
        return _fallback_response(
            query,
            chunks,
            "Qwen inference is unavailable. No grounded legal answer was generated.",
            service_error=True,
        )

    citations = citations_from_chunks(chunks)
    provider_answer["citations"] = citations
    provider_answer["source"] = citations[0] if citations else None
    provider_answer["fallback_used"] = False
    provider_answer["service_error"] = False
    provider_answer["query"] = query
    provider_answer["disclaimer"] = "This is legal awareness information, not legally verified advice."
    provider_answer.pop("confidence", None)
    return provider_answer
