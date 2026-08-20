"""
Ingestion script for Nyaya Setu legal knowledge base.

Uses the pipeline:
Loaders -> Cleaner -> Chunker -> Classifier (InLegalBERT) -> Metadata -> Embedder -> Indexer
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import BACKEND_ROOT
from backend.rag.ingestion import ingest_source_dir

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Nyaya Setu knowledge base.")
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=BACKEND_ROOT / "data" / "source_docs",
        help="Folder containing PDFs, HTML, TXT, or JSON source documents.",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Recreate the Qdrant collection instead of appending.",
    )
    args = parser.parse_args()
    records = ingest_source_dir(args.source_dir, rebuild=args.rebuild)
    logger.info("Ingestion finished with %d records.", len(records))


if __name__ == "__main__":
    main()
