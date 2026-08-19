"""
Ingestion script for Nyaya Setu legal knowledge base.

Uses the pipeline:
Loaders -> Cleaner -> Chunker -> Classifier (InLegalBERT) -> Metadata -> Embedder -> Indexer
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.rag.ingestion import (
    load_directory, RawDocument,
    clean_pages,
    chunk_document, LegalChunk,
    classify_batch,
    enrich_chunks,
    embed_texts,
    index_bm25, index_qdrant,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Default paths for corpus snapshot
CORPUS_DIR = Path("data/corpus")
CORPUS_JSON = CORPUS_DIR / "corpus.json"


def _ensure_dirs() -> None:
    """Ensure output directories exist."""
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)


def _save_json_records(records: list[dict[str, Any]]) -> None:
    """Save records to a JSON snapshot (without embeddings to keep it readable)."""
    serializable = []
    for r in records:
        entry = {k: v for k, v in r.items() if k != "embedding"}
        serializable.append(entry)
    CORPUS_JSON.write_text(json.dumps(serializable, indent=2, ensure_ascii=False), encoding="utf-8")


def process_document(doc: RawDocument) -> list[LegalChunk]:
    """Clean and chunk a single loaded document."""
    cleaned_pages = clean_pages(doc.pages)
    if not cleaned_pages:
        return []
        
    return chunk_document(
        document_id=doc.document_id,
        document_name=doc.document_name,
        source=doc.source,
        source_url=doc.source_url,
        pages=cleaned_pages,
        language="en",
    )


def ingest(source_dir: Path, rebuild: bool = False) -> list[dict[str, Any]]:
    """Run the full ingestion pipeline."""
    _ensure_dirs()
    
    # 1. Load documents
    logger.info("Loading documents from %s...", source_dir)
    docs = load_directory(source_dir)
    logger.info("Loaded %d documents", len(docs))
    
    if not docs:
        logger.warning("No documents found. Nothing to ingest.")
        return []
    
    # 2. Clean and Chunk
    logger.info("Cleaning and chunking...")
    all_chunks: list[LegalChunk] = []
    for doc in docs:
        chunks = process_document(doc)
        all_chunks.extend(chunks)
    logger.info("Created %d chunks", len(all_chunks))
    
    if not all_chunks:
        logger.warning("No chunks generated. Nothing to classify or index.")
        return []
    
    # 3. Classify with InLegalBERT
    logger.info("Running InLegalBERT classification...")
    texts_to_classify = [c.original_text for c in all_chunks]
    classifications = classify_batch(texts_to_classify)
    logger.info("Chunks classified: %d", len(classifications))
    
    # 4. Enrich metadata
    logger.info("Enriching metadata...")
    records = enrich_chunks(all_chunks, classifications)
    
    # Deduplicate by chunk_id
    deduped: dict[str, dict[str, Any]] = {}
    for record in records:
        chunk_id = str(record.get("chunk_id", ""))
        if chunk_id:
            deduped[chunk_id] = record
    final_records = list(deduped.values())
    
    # 5. Embed with existing multilingual model
    logger.info("Generating embeddings for %d records...", len(final_records))
    embed_texts_list = [
        " ".join(
            part
            for part in [
                r.get("section", ""),
                r.get("topic", ""),
                r.get("original_text", ""),
            ]
            if part
        )
        for r in final_records
    ]
    embeddings = embed_texts(embed_texts_list)
    for record, vector in zip(final_records, embeddings):
        record["embedding"] = vector
        
    # Save JSON snapshot
    _save_json_records(final_records)
    logger.info("Saved %d records to %s", len(final_records), CORPUS_JSON)
    
    # 6. Index (Qdrant + BM25)
    logger.info("Indexing into Qdrant...")
    upserted = index_qdrant(final_records, recreate=rebuild)
    
    logger.info("Building BM25 index...")
    indexed_bm25 = index_bm25(final_records)
    
    # Final summary
    logger.info("=" * 50)
    logger.info("Ingestion complete.")
    logger.info("  Documents processed: %d", len(docs))
    logger.info("  Chunks created: %d", len(all_chunks))
    logger.info("  Chunks classified: %d", len(classifications))
    logger.info("  Qdrant indexed: %d", upserted)
    logger.info("  BM25 indexed: %d", indexed_bm25)
    logger.info("=" * 50)
    
    return final_records


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Nyaya Setu knowledge base.")
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path("data/source_docs"),
        help="Folder containing PDFs, HTML, TXT, or JSON source documents.",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Recreate the Qdrant collection instead of appending.",
    )
    args = parser.parse_args()
    
    ingest(args.source_dir, rebuild=args.rebuild)


if __name__ == "__main__":
    main()

