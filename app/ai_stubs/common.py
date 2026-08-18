from __future__ import annotations

from functools import lru_cache
import json
import math
import re
from typing import Any

from app.config import SETTINGS


TOKEN_RE = re.compile(r"[a-zA-Z0-9]+", re.UNICODE)


def normalize_text(text: str) -> str:
    return " ".join(text.strip().split())


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def simple_embedding(text: str, dimensions: int = 128) -> list[float]:
    vector = [0.0] * dimensions
    for token in tokenize(text):
        bucket = hash(token) % dimensions
        vector[bucket] += 1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    size = min(len(left), len(right))
    if not size:
        return 0.0
    dot = sum(left[i] * right[i] for i in range(size))
    left_norm = math.sqrt(sum(value * value for value in left[:size])) or 1.0
    right_norm = math.sqrt(sum(value * value for value in right[:size])) or 1.0
    return dot / (left_norm * right_norm)


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
            fragment = candidate[start : end + 1]
            try:
                return json.loads(fragment)
            except json.JSONDecodeError:
                continue
    return None


def chunk_text(text: str, max_chars: int = 900) -> list[str]:
    text = normalize_text(text)
    if not text:
        return []
    paragraphs = re.split(r"\n\s*\n+", text)
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        candidate = f"{current} {paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(paragraph) <= max_chars:
            current = paragraph
        else:
            sentences = re.split(r"(?<=[.!?])\s+", paragraph)
            temp = ""
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                candidate = f"{temp} {sentence}".strip() if temp else sentence
                if len(candidate) <= max_chars:
                    temp = candidate
                else:
                    if temp:
                        chunks.append(temp)
                    temp = sentence
            current = temp
    if current:
        chunks.append(current)
    return chunks


def heuristic_simplify(text: str) -> str:
    text = normalize_text(text)
    if not text:
        return ""
    sentence = re.split(r"(?<=[.!?])\s+", text)[0]
    if len(sentence) > 260:
        sentence = sentence[:257].rsplit(" ", 1)[0] + "..."
    return sentence


@lru_cache(maxsize=1)
def get_threshold() -> float:
    return SETTINGS.confidence_threshold


def extract_first_number(text: str) -> str | None:
    match = re.search(r"\b(\d+)\b", text)
    return match.group(1) if match else None


def score_overlap(query: str, candidate: str) -> float:
    q_tokens = set(tokenize(query))
    c_tokens = set(tokenize(candidate))
    if not q_tokens or not c_tokens:
        return 0.0
    intersection = len(q_tokens & c_tokens)
    return intersection / max(1, len(q_tokens))

