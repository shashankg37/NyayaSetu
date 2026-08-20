"""Provider-agnostic LLM interface for NyayaSetu.

Primary path: Groq (Qwen). Hugging Face and Gemini remain optional fallbacks.
"""
from __future__ import annotations

import base64
import json
import logging
import re
from typing import Any, Protocol

import requests

from backend.config import SETTINGS

logger = logging.getLogger(__name__)


class LLMUnavailableError(RuntimeError):
    """Raised when no configured inference provider can generate a response."""


def safe_json_loads(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    # Strip <think>...</think> block if present (useful for reasoning models)
    cleaned_text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Also strip open-ended think tag if it didn't close
    cleaned_text = re.sub(r"<think>.*", "", cleaned_text, flags=re.DOTALL)

    candidates = [cleaned_text]
    if "```" in cleaned_text:
        candidates.extend(segment for segment in cleaned_text.split("```") if segment.strip())
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
    seen: set[tuple[Any, Any, Any, Any]] = set()
    for chunk in chunks:
        document_name = chunk.get("document_name") or chunk.get("act") or chunk.get("source")
        act = chunk.get("act") or document_name
        section = chunk.get("section") or None
        page = chunk.get("page")
        year = chunk.get("year")
        url = chunk.get("source_url") or None
        key = (act, section, page, year)
        if not document_name and not act:
            continue
        if key in seen:
            continue
        seen.add(key)
        citations.append(
            {
                "document_name": document_name,
                "act": act,
                "law": act,
                "section": section,
                "page": page,
                "year": year,
                "source": chunk.get("source") or document_name,
                "source_url": url,
            }
        )
    return citations


class LLMProvider(Protocol):
    def generate(self, prompt: str, **kwargs: Any) -> str | None: ...
    def generate_json(self, prompt: str, **kwargs: Any) -> dict[str, Any] | None: ...
    def generate_json_with_image(self, prompt: str, image_bytes: bytes, mime_type: str, **kwargs: Any) -> dict[str, Any] | None: ...


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
        """Generate text through Hugging Face Inference Providers."""
        if not SETTINGS.hf_api_key:
            logger.warning("HF API key missing")
            return None

        max_tokens = int(
            kwargs.get("max_new_tokens")
            or kwargs.get("max_tokens")
            or 1000
        )
        temperature = float(kwargs.get("temperature", 0.1))

        try:
            from huggingface_hub import InferenceClient  # type: ignore

            client = InferenceClient(
                provider=getattr(SETTINGS, "hf_provider", "featherless-ai"),
                api_key=SETTINGS.hf_api_key,
            )

            logger.info(
                "Hugging Face provider=%s model=%s",
                getattr(SETTINGS, "hf_provider", "featherless-ai"),
                SETTINGS.llm_model,
            )

            completion = client.chat.completions.create(
                model=SETTINGS.llm_model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )

            content = completion.choices[0].message.content

            if isinstance(content, str) and content.strip():
                return content.strip()

            if isinstance(content, list):
                parts = [
                    str(part.get("text", ""))
                    for part in content
                    if isinstance(part, dict)
                ]
                text = "".join(parts).strip()
                return text or None

            return None

        except Exception as exc:
            logger.error("Hugging Face generation failed: %s", exc)
            return None

    def generate_json(self, prompt: str, **kwargs: Any) -> dict[str, Any] | None:
        json_prompt = f"{prompt}\n\nRespond ONLY with valid JSON. Do not include markdown fences."
        text = self.generate(json_prompt, **kwargs)
        return safe_json_loads(text or "")

    def generate_json_with_image(self, prompt: str, image_bytes: bytes, mime_type: str, **kwargs: Any) -> dict[str, Any] | None:
        if not SETTINGS.hf_api_key:
            logger.warning("HF API key missing")
            return None
        data_url = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
        max_tokens = int(kwargs.get("max_new_tokens") or kwargs.get("max_tokens") or 1000)
        temperature = float(kwargs.get("temperature", 0.1))
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"{prompt}\n\nRespond ONLY with valid JSON. Do not include markdown fences."},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ]
        try:
            from huggingface_hub import InferenceClient  # type: ignore

            client = InferenceClient(token=SETTINGS.hf_api_key)
            completion = client.chat.completions.create(
                model=SETTINGS.llm_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            content = completion.choices[0].message.content
            return safe_json_loads(str(content or ""))
        except Exception as hub_error:
            logger.info("HF multimodal chat client failed, trying HTTP inference: %s", hub_error)

        headers = {"Authorization": f"Bearer {SETTINGS.hf_api_key}"}
        url = f"{SETTINGS.hf_api_url.rstrip('/')}/{SETTINGS.llm_model}"
        payload = {
            "model": SETTINGS.llm_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=90)
            if response.status_code >= 400:
                logger.warning("HF multimodal HTTP %s: %s", response.status_code, response.text[:300])
                return None
            return safe_json_loads(_chat_text_from_hf(response.json()) or "")
        except Exception as exc:
            logger.error("HuggingFace multimodal generation failed: %s", exc)
            return None


class GroqProvider:
    """Groq OpenAI-compatible chat completion provider for Qwen."""

    def generate(self, prompt: str, **kwargs: Any) -> str | None:
        if not SETTINGS.groq_api_key:
            logger.warning("Groq API key missing")
            return None

        max_tokens = int(
            kwargs.get("max_new_tokens")
            or kwargs.get("max_tokens")
            or 4000
        )
        temperature = float(kwargs.get("temperature", 0.1))

        try:
            from groq import Groq  # type: ignore

            client = Groq(api_key=SETTINGS.groq_api_key)
            logger.info("Groq model=%s", SETTINGS.groq_model)
            completion = client.chat.completions.create(
                model=SETTINGS.groq_model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            content = completion.choices[0].message.content
            if isinstance(content, str) and content.strip():
                return content.strip()
            if isinstance(content, list):
                parts = [
                    str(part.get("text", ""))
                    for part in content
                    if isinstance(part, dict)
                ]
                text = "".join(parts).strip()
                return text or None
            return None
        except Exception as exc:
            logger.error("Groq generation failed: %s", exc)
            return None

    def generate_json(self, prompt: str, **kwargs: Any) -> dict[str, Any] | None:
        json_prompt = f"{prompt}\n\nRespond ONLY with valid JSON. Do not include markdown fences."
        text = self.generate(json_prompt, **kwargs)
        return safe_json_loads(text or "")

    def generate_json_with_image(self, prompt: str, image_bytes: bytes, mime_type: str, **kwargs: Any) -> dict[str, Any] | None:
        return None


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

    def generate_json_with_image(self, prompt: str, image_bytes: bytes, mime_type: str, **kwargs: Any) -> dict[str, Any] | None:
        return None


class LocalProvider:
    def generate(self, prompt: str, **kwargs: Any) -> str | None:
        logger.error("Local provider is not configured for Qwen inference.")
        return None

    def generate_json(self, prompt: str, **kwargs: Any) -> dict[str, Any] | None:
        return None

    def generate_json_with_image(self, prompt: str, image_bytes: bytes, mime_type: str, **kwargs: Any) -> dict[str, Any] | None:
        return None


_PROVIDERS: dict[str, LLMProvider] = {
    "groq": GroqProvider(),
    "hf": HuggingFaceProvider(),
    "gemini": GeminiProvider(),
    "local": LocalProvider(),
}


def get_provider(name: str | None = None) -> LLMProvider:
    provider_name = name or SETTINGS.llm_provider
    return _PROVIDERS.get(provider_name) or _PROVIDERS["groq"]


def generate_json_from_any(prompt: str) -> dict[str, Any] | None:
    return get_provider().generate_json(prompt)


def generate_text_from_any(prompt: str) -> str | None:
    return get_provider().generate(prompt)


def generate_json_from_image(prompt: str, image_bytes: bytes, mime_type: str) -> dict[str, Any] | None:
    return HuggingFaceProvider().generate_json_with_image(prompt, image_bytes, mime_type)


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
                    f"year: {chunk.get('year', '')}",
                    f"language: {chunk.get('language', '')}",
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
        "You are Nyaya Setu, an Indian legal-awareness assistant.\n"
        "Answer using ONLY the supplied official evidence chunks.\n"
        "Rules:\n"
        "- Do not use general knowledge to fill legal gaps.\n"
        "- Do not invent acts, sections, cases, years, pages, or URLs.\n"
        "- If a fact is not in the evidence, say it is not in the supplied sources.\n"
        "- State uncertainty clearly when the evidence is incomplete.\n"
        "- Distinguish legal information from professional legal advice.\n"
        "- Refer to sources only by the metadata provided with each chunk "
        "(document/act, section, page, year). Do not create citations.\n"
        "Return JSON with keys: your_right, what_law_says, what_this_means, "
        "what_you_can_do (array), interpretation, next_action, uncertainty. "
        "Do not include a numeric confidence score. Do not include a citations array.\n\n"
        f"Conversation:\n{history_text}\n\nQuestion:\n{query}\n\n"
        f"User document extraction (not law):\n{extracted}\n\nOfficial evidence:\n{_build_context(chunks)}"
    )
    provider = get_provider()
    # Safe logging of provider and model (NEVER log the API key)
    logger.info("LLM provider: %s", getattr(SETTINGS, "llm_provider", "unknown"))
    if getattr(SETTINGS, "llm_provider", None) == "groq":
        logger.info("LLM model: %s", getattr(SETTINGS, "groq_model", "unknown"))
    elif getattr(SETTINGS, "llm_provider", None) == "hf":
        logger.info("LLM model: %s", getattr(SETTINGS, "llm_model", "unknown"))
    elif getattr(SETTINGS, "llm_provider", None) == "gemini":
        logger.info("LLM model: %s", getattr(SETTINGS, "gemini_model", "unknown"))
    else:
        logger.info("LLM model: unknown")

    provider_answer = provider.generate_json(prompt)
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
