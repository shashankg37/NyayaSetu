"""
Ingestion script for Nyaya Setu legal knowledge base.

Uses the pipeline:
Loaders -> Cleaner -> Chunker -> Classifier (InLegalBERT) -> Metadata -> Embedder -> Indexer
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

from app.ai.knowledge_base.store import ensure_kb_dirs, load_seed_records, save_json_records
from app.ingestion.chunker import chunk_document, LegalChunk
from app.ingestion.classifier import classify_batch
from app.ingestion.cleaner import clean_pages
from app.ingestion.embedder import embed_texts
from app.ingestion.indexer import index_bm25, index_qdrant
from app.ingestion.loaders import load_directory, RawDocument
from app.ingestion.metadata import enrich_chunks

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


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
    ensure_kb_dirs()
    
    # 1. Load documents
    logger.info("Loading documents from %s", source_dir)
    docs = load_directory(source_dir)
    logger.info("Loaded %d documents", len(docs))
    
    # 2. Clean and Chunk
    logger.info("Cleaning and chunking...")
    all_chunks: list[LegalChunk] = []
    for doc in docs:
        chunks = process_document(doc)
        all_chunks.extend(chunks)
    logger.info("Generated %d chunks from files", len(all_chunks))
    
    # 3. Classify
    logger.info("Classifying chunks with InLegalBERT (this may take a while)...")
    texts_to_classify = [c.original_text for c in all_chunks]
    classifications = classify_batch(texts_to_classify)
    
    # 4. Enrich metadata
    logger.info("Enriching metadata...")
    records = enrich_chunks(all_chunks, classifications)
    
    # Add seed records (already processed/mocked)
    seed_records = load_seed_records()
    if seed_records:
        logger.info("Adding %d seed records", len(seed_records))
        records.extend(seed_records)
        
    # Deduplicate by chunk_id
    deduped: dict[str, dict[str, Any]] = {}
    for record in records:
        chunk_id = str(record.get("chunk_id", ""))
        if chunk_id:
            deduped[chunk_id] = record
    final_records = list(deduped.values())
    
    # 5. Embed
    logger.info("Generating embeddings for %d records...", len(final_records))
    embed_texts_list = [
        " ".join(
            part
            for part in [
                r.get("act", ""),
                r.get("section", ""),
                r.get("topic", ""),
                r.get("original_text", ""),
                r.get("simplified_text", "")
            ]
            if part
        )
        for r in final_records
    ]
    embeddings = embed_texts(embed_texts_list)
    for record, vector in zip(final_records, embeddings):
        record["embedding"] = vector
        
    # Save JSON snapshot
    save_json_records(final_records)
    logger.info("Saved %d records to corpus.json", len(final_records))
    
    # 6. Index (Qdrant + BM25)
    logger.info("Indexing into Qdrant...")
    upserted = index_qdrant(final_records, recreate=rebuild)
    
    logger.info("Indexing into BM25...")
    indexed_bm25 = index_bm25(final_records)
    
    logger.info("Ingestion complete. Qdrant points: %d, BM25 docs: %d", upserted, indexed_bm25)
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
