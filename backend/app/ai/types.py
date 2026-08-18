from __future__ import annotations

from typing import Any, TypedDict


class PipelineState(TypedDict, total=False):
    input_type: str
    text: str
    audio_bytes: bytes
    image_bytes: bytes
    normalized_text: str
    intent: str
    chunks: list[dict[str, Any]]
    answer: dict[str, Any]
    document: dict[str, Any]

