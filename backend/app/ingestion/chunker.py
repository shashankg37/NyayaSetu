"""Legal-aware chunking for Indian legal documents.

Preserves document structure: section/subsection boundaries, numbered clauses,
and paragraph context. Each chunk has a stable chunk_id and full provenance.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any


# Indian legal section patterns
_SECTION_RE = re.compile(
    r"^(?:"
    r"(?:Section|Sec\.?|S\.?)\s+\d+[A-Za-z]?"  # Section 5, Sec. 12A
    r"|CHAPTER\s+[IVXLCDM\d]+"                    # CHAPTER III
    r"|PART\s+[IVXLCDM]+"                          # PART IV
    r"|SCHEDULE\s+[IVXLCDM\d]*"                    # SCHEDULE I
    r"|Article\s+\d+"                               # Article 21
    r"|\d+[A-Za-z]?\.\s"                           # 5. or 12A.
    r")",
    re.IGNORECASE | re.MULTILINE,
)

_SUBSECTION_RE = re.compile(
    r"^\s*\((\d+|[a-z]|[ivxlcdm]+)\)\s",
    re.IGNORECASE | re.MULTILINE,
)

_PARAGRAPH_SEP_RE = re.compile(r"\n\s*\n+")

MAX_CHUNK_CHARS = 900
MIN_CHUNK_CHARS = 100


@dataclass
class LegalChunk:
    """A single chunk of legal text with full provenance."""
    chunk_id: str
    document_id: str
    document_name: str
    source: str
    source_url: str
    page: int | None
    section: str
    subsection: str
    original_text: str
    language: str = "en"
    metadata: dict[str, Any] = field(default_factory=dict)


def _stable_chunk_id(document_id: str, section: str, chunk_index: int) -> str:
    """Generate a stable, reproducible chunk ID."""
    raw = f"{document_id}::{section}::{chunk_index}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _detect_section(text: str) -> str:
    """Try to detect a section heading in a text block."""
    match = _SECTION_RE.match(text.strip())
    if match:
        return match.group(0).strip().rstrip(".")
    return ""


def _detect_subsection(text: str) -> str:
    """Try to detect a subsection marker."""
    match = _SUBSECTION_RE.match(text.strip())
    if match:
        return f"({match.group(1)})"
    return ""


def _split_into_blocks(text: str) -> list[str]:
    """Split text into paragraph-level blocks."""
    blocks = _PARAGRAPH_SEP_RE.split(text)
    return [block.strip() for block in blocks if block.strip()]


def _merge_small_blocks(blocks: list[str], max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Merge consecutive small blocks, respecting max_chars.

    Tries to keep blocks together when they're below MIN_CHUNK_CHARS,
    and never exceeds max_chars.
    """
    if not blocks:
        return []

    merged: list[str] = []
    current = blocks[0]

    for block in blocks[1:]:
        candidate = f"{current}\n\n{block}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                merged.append(current)
            current = block

    if current:
        merged.append(current)

    return merged


def _split_oversized(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split an oversized block into sentence-level chunks."""
    if len(text) <= max_chars:
        return [text]

    # Try splitting on sentence boundaries
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            # If a single sentence is too long, split on clause boundaries
            if len(sentence) > max_chars:
                clause_parts = re.split(r"[;,]\s+", sentence)
                for part in clause_parts:
                    if len(part) <= max_chars:
                        chunks.append(part)
                    else:
                        # Last resort: hard split
                        for i in range(0, len(part), max_chars):
                            chunks.append(part[i : i + max_chars])
                current = ""
            else:
                current = sentence

    if current:
        chunks.append(current)

    return chunks


def chunk_document(
    document_id: str,
    document_name: str,
    source: str,
    source_url: str,
    pages: list[str],
    language: str = "en",
    max_chars: int = MAX_CHUNK_CHARS,
) -> list[LegalChunk]:
    """Chunk a legal document with section/subsection awareness.

    Each page is processed independently to maintain page provenance.
    Within each page, section and subsection boundaries are detected.
    """
    chunks: list[LegalChunk] = []
    chunk_index = 0
    current_section = "Preamble"
    current_subsection = ""

    for page_num, page_text in enumerate(pages, start=1):
        if not page_text.strip():
            continue

        blocks = _split_into_blocks(page_text)

        for block in blocks:
            # Detect section/subsection boundaries
            detected_section = _detect_section(block)
            if detected_section:
                current_section = detected_section
                current_subsection = ""

            detected_sub = _detect_subsection(block)
            if detected_sub:
                current_subsection = detected_sub

            # Split oversized blocks, then merge small ones
            sub_blocks = _split_oversized(block, max_chars)

            for text_piece in sub_blocks:
                if len(text_piece.strip()) < 20:
                    continue  # Skip very short fragments

                chunk_index += 1
                chunk_id = _stable_chunk_id(document_id, current_section, chunk_index)

                chunks.append(
                    LegalChunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        document_name=document_name,
                        source=source,
                        source_url=source_url,
                        page=page_num,
                        section=current_section,
                        subsection=current_subsection,
                        original_text=text_piece.strip(),
                        language=language,
                    )
                )

    return chunks


def chunk_text_simple(
    text: str,
    document_id: str = "unknown",
    document_name: str = "unknown",
    source: str = "unknown",
    source_url: str = "",
    max_chars: int = MAX_CHUNK_CHARS,
) -> list[LegalChunk]:
    """Chunk plain text (not page-separated) into legal chunks."""
    return chunk_document(
        document_id=document_id,
        document_name=document_name,
        source=source,
        source_url=source_url,
        pages=[text],
        max_chars=max_chars,
    )
