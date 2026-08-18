"""Metadata enrichment for legal chunks.

Combines loader metadata, classifier tags, and chunk provenance
into the final metadata structure stored alongside each chunk.
"""
from __future__ import annotations

from typing import Any

from app.ingestion.chunker import LegalChunk


def build_chunk_metadata(
    chunk: LegalChunk,
    classification: dict[str, Any],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the full metadata payload for a chunk.

    This is the authoritative metadata schema stored in Qdrant and the corpus.
    """
    metadata: dict[str, Any] = {
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "document_name": chunk.document_name,
        "source": chunk.source,
        "source_url": chunk.source_url,
        "page": chunk.page,
        "section": chunk.section,
        "subsection": chunk.subsection,
        "topic": classification.get("topic", "general"),
        "legal_domain": classification.get("legal_domain", "general"),
        "beneficiary": classification.get("beneficiary", "citizen"),
        "jurisdiction": "india",
        "language": chunk.language,
        "original_text": chunk.original_text,
        # We do NOT replace the original text with AI summaries.
        # The simplified_text is just a searchability aid.
        "simplified_text": "",
        "domain_confidence": classification.get("domain_confidence", 0.0),
        "topic_confidence": classification.get("topic_confidence", 0.0),
        "beneficiary_confidence": classification.get("beneficiary_confidence", 0.0),
    }

    if extra:
        for key, value in extra.items():
            if key not in metadata:
                metadata[key] = value

    return metadata


def enrich_chunks(
    chunks: list[LegalChunk],
    classifications: list[dict[str, Any]],
    extra: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Enrich a list of chunks with classification metadata.

    Args:
        chunks: Legal chunks from the chunker.
        classifications: Classification results from the classifier (same order/length).
        extra: Optional extra metadata to add to every chunk.

    Returns:
        List of fully enriched metadata dicts ready for indexing.
    """
    if len(chunks) != len(classifications):
        raise ValueError(
            f"Chunks ({len(chunks)}) and classifications ({len(classifications)}) must be same length"
        )

    return [
        build_chunk_metadata(chunk, classification, extra)
        for chunk, classification in zip(chunks, classifications)
    ]
