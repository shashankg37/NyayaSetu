from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any
import json
import re

from app.ai_stubs.common import chunk_text, heuristic_simplify, normalize_text
from app.config import CORPUS_PATH, KB_DIR, QDRANT_DIR, SAMPLE_CORPUS_PATH, SETTINGS
from app.knowledge_base.store import (
    ChunkRecord,
    ensure_kb_dirs,
    load_json_records,
    load_seed_records,
    save_json_records,
    save_pickle,
)


def _extract_text_from_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                return "\n\n".join(
                    " ".join(str(value) for value in item.values() if isinstance(value, (str, int, float)))
                    for item in payload
                    if isinstance(item, dict)
                )
            if isinstance(payload, dict):
                return " ".join(str(value) for value in payload.values() if isinstance(value, (str, int, float)))
        except Exception:
            return ""
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(str(path))
            pages = []
            for page in reader.pages:
                pages.append(page.extract_text() or "")
            return "\n".join(pages)
        except Exception:
            return ""
    if suffix in {".html", ".htm"}:
        try:
            from bs4 import BeautifulSoup  # type: ignore

            return BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser").get_text(" ")
        except Exception:
            return ""
    return ""


def _source_to_metadata(path: Path, text: str) -> dict[str, str]:
    lower = f"{path.stem} {text[:1200]}".lower()
    topic = "general"
    if any(marker in lower for marker in ["wage", "salary", "employ", "labour", "worker"]):
        topic = "labour"
    elif any(marker in lower for marker in ["tenant", "landlord", "rent", "evict"]):
        topic = "housing"
    elif any(marker in lower for marker in ["family", "marriage", "child", "maintenance"]):
        topic = "family"
    elif any(marker in lower for marker in ["consumer", "purchase", "refund"]):
        topic = "consumer"
    return {"source": path.stem, "topic": topic, "source_url": path.as_uri()}


def _build_records_from_text(source_name: str, text: str, metadata: dict[str, str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    chunks = chunk_text(text)
    for index, chunk in enumerate(chunks, start=1):
        simplified = _simplify_chunk(chunk)
        record = ChunkRecord(
            chunk_id=f"{source_name}_{index}",
            source=metadata["source"],
            act=source_name,
            section=f"Chunk {index}",
            topic=metadata["topic"],
            original_text=chunk,
            simplified_text=simplified,
            source_url=metadata["source_url"],
            page=index,
        )
        records.append(record.to_dict())
    return records


def _simplify_chunk(text: str) -> str:
    try:
        import google.generativeai as genai  # type: ignore
    except Exception:
        return heuristic_simplify(text)
    api_key = getattr(SETTINGS, "gemini_api_key", "")
    if not api_key:
        return heuristic_simplify(text)
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(SETTINGS.gemini_model)
        prompt = (
            "Rewrite this legal text in plain language in one or two sentences. "
            "Do not invent new facts.\n\n"
            f"Text: {text}"
        )
        response = model.generate_content(prompt)
        simplified = getattr(response, "text", "").strip()
        return simplified or heuristic_simplify(text)
    except Exception:
        return heuristic_simplify(text)


def _embed_record(text: str) -> list[float]:
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        model = SentenceTransformer(SETTINGS.embedding_model)
        vector = model.encode([text], normalize_embeddings=True)[0]
        return vector.tolist() if hasattr(vector, "tolist") else list(vector)
    except Exception:
        from app.ai_stubs.common import simple_embedding

        return simple_embedding(text)


def _prepare_qdrant(records: list[dict[str, Any]]) -> None:
    try:
        from qdrant_client import QdrantClient  # type: ignore
        from qdrant_client.http import models as rest  # type: ignore
    except Exception:
        return
    if not records:
        return
    QDRANT_DIR.mkdir(parents=True, exist_ok=True)
    client = QdrantClient(path=str(QDRANT_DIR))
    vector_size = len(records[0].get("embedding", [])) or 128
    if not client.collection_exists(SETTINGS.qdrant_collection):
        client.create_collection(
            collection_name=SETTINGS.qdrant_collection,
            vectors_config=rest.VectorParams(size=vector_size, distance=rest.Distance.COSINE),
        )
    points = []
    for idx, record in enumerate(records):
        points.append(
            rest.PointStruct(
                id=idx,
                vector=record["embedding"],
                payload={key: value for key, value in record.items() if key != "embedding"},
            )
        )
    client.upsert(collection_name=SETTINGS.qdrant_collection, points=points)


def _build_bm25(records: list[dict[str, Any]]) -> None:
    try:
        from rank_bm25 import BM25Okapi  # type: ignore
    except Exception:
        return
    from app.ai_stubs.common import tokenize

    corpus = [tokenize(f"{record.get('original_text', '')} {record.get('simplified_text', '')}") for record in records]
    bm25 = BM25Okapi(corpus)
    save_pickle(bm25)


def ingest(source_dir: Path | None = None) -> list[dict[str, Any]]:
    ensure_kb_dirs()
    records: list[dict[str, Any]] = []
    records.extend(load_seed_records())
    if source_dir and source_dir.exists():
        for path in sorted(source_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".txt", ".json", ".pdf", ".html", ".htm"}:
                continue
            text = normalize_text(_extract_text_from_file(path))
            if not text:
                continue
            metadata = _source_to_metadata(path, text)
            source_records = _build_records_from_text(path.stem, text, metadata)
            records.extend(source_records)
    deduped: dict[str, dict[str, Any]] = {}
    for record in records:
        chunk_id = str(record.get("chunk_id"))
        if chunk_id:
            deduped[chunk_id] = record
    final_records = list(deduped.values())
    for record in final_records:
        record["embedding"] = _embed_record(
            " ".join(
                part
                for part in [
                    record.get("act", ""),
                    record.get("section", ""),
                    record.get("original_text", ""),
                    record.get("simplified_text", ""),
                ]
                if part
            )
        )
    save_json_records(final_records)
    _prepare_qdrant(final_records)
    _build_bm25(final_records)
    return final_records


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Nyaya Setu knowledge base.")
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path("data/source_docs"),
        help="Folder containing PDFs, HTML, TXT, or JSON source documents.",
    )
    args = parser.parse_args()
    records = ingest(args.source_dir)
    print(f"Ingested {len(records)} chunks into the local knowledge base.")


if __name__ == "__main__":
    main()

