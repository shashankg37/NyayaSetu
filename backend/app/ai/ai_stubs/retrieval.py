from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
from typing import Any
import math

from app.ai.ai_stubs.common import cosine_similarity, score_overlap, simple_embedding, tokenize
from app.ai.config import CORPUS_PATH, QDRANT_DIR, SETTINGS
from app.ai.knowledge_base.store import load_json_records, load_pickle, load_seed_records, make_source_label, record_text


def _load_records() -> list[dict[str, Any]]:
    records = load_json_records(CORPUS_PATH)
    return records or load_seed_records()


@lru_cache(maxsize=1)
def _records_cache() -> tuple[dict[str, Any], ...]:
    return tuple(_load_records())


@lru_cache(maxsize=1)
def _embedding_backend() -> Any:
    try:
        from langchain_huggingface import HuggingFaceEmbeddings  # type: ignore

        return HuggingFaceEmbeddings(
            model_name=SETTINGS.embedding_model,
            encode_kwargs={"normalize_embeddings": True},
        )
    except Exception:
        return None


def _embed_text(text: str) -> list[float]:
    backend = _embedding_backend()
    if backend is not None:
        try:
            return list(backend.embed_query(text))
        except Exception:
            pass
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        model = SentenceTransformer(SETTINGS.embedding_model)
        vector = model.encode([text], normalize_embeddings=True)[0]
        return vector.tolist() if hasattr(vector, "tolist") else list(vector)
    except Exception:
        return simple_embedding(text)


def _document_to_record(document: Any) -> dict[str, Any]:
    if isinstance(document, dict):
        return dict(document)
    metadata = dict(getattr(document, "metadata", {}) or {})
    if getattr(document, "page_content", None):
        metadata.setdefault("simplified_text", document.page_content)
    return metadata


def _manual_dense_search(query: str, top_k: int) -> list[dict[str, Any]]:
    query_vector = _embed_text(query)
    scored = []
    for record in _records_cache():
        text = record_text(record)
        vector = record.get("embedding") or _embed_text(text)
        scored.append((cosine_similarity(query_vector, vector), record))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [{**dict(record), "dense_score": float(score), "retrieval_score": float(score)} for score, record in scored[:top_k]]


def _build_dense_candidates(query: str, top_k: int = 20) -> list[dict[str, Any]]:
    try:
        from langchain_community.vectorstores import Qdrant as LCQdrant  # type: ignore

        if QDRANT_DIR.exists():
            embeddings = _embedding_backend()
            if embeddings is None:
                raise RuntimeError("LangChain embeddings are unavailable")
            store = LCQdrant(
                client=None,
                collection_name=SETTINGS.qdrant_collection,
                embeddings=embeddings,
                path=str(QDRANT_DIR),
            )
            return [
                {**_document_to_record(doc), "dense_score": float(score), "retrieval_score": float(score)}
                for doc, score in store.similarity_search_with_score(query, k=top_k)
            ]
    except Exception:
        pass
    return _manual_dense_search(query, top_k)


def _manual_bm25_search(query: str, top_k: int) -> list[dict[str, Any]]:
    scored = []
    for record in _records_cache():
        scored.append((score_overlap(query, record_text(record)), record))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [{**dict(record), "bm25_score": float(score), "retrieval_score": float(score)} for score, record in scored[:top_k]]


def _build_bm25_candidates(query: str, top_k: int = 20) -> list[dict[str, Any]]:
    try:
        from langchain_community.retrievers import BM25Retriever  # type: ignore
        from langchain_core.documents import Document  # type: ignore

        docs = [
            Document(page_content=record.get("simplified_text") or record.get("original_text") or "", metadata=dict(record))
            for record in _records_cache()
        ]
        retriever = BM25Retriever.from_documents(docs)
        retriever.k = top_k
        return [
            {**_document_to_record(doc), "bm25_score": float(1.0 / rank), "retrieval_score": float(1.0 / rank)}
            for rank, doc in enumerate(retriever.invoke(query), start=1)
        ]
    except Exception:
        return _manual_bm25_search(query, top_k)


def _rrf_merge(*ranked_lists: list[dict[str, Any]], k: int = 60) -> list[dict[str, Any]]:
    fused: dict[str, dict[str, Any]] = {}
    weights: defaultdict[str, float] = defaultdict(float)
    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, start=1):
            chunk_id = item.get("chunk_id") or f"{item.get('act')}::{item.get('section')}"
            weights[chunk_id] += 1.0 / (k + rank)
            fused.setdefault(chunk_id, dict(item))
    merged = []
    for chunk_id, item in fused.items():
        item["rrf_score"] = float(weights[chunk_id])
        merged.append(item)
    merged.sort(key=lambda entry: entry.get("rrf_score", 0.0), reverse=True)
    return merged


def _manual_rerank(query: str, candidates: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
    scored_candidates = []
    for record in candidates:
        text = record.get("simplified_text") or record_text(record)
        overlap = score_overlap(query, text)
        confidence = max(0.05, min(0.95, 0.35 + 0.6 * overlap))
        item = dict(record)
        item["confidence"] = confidence
        item["reranker_score"] = confidence
        scored_candidates.append(item)
    scored_candidates.sort(key=lambda entry: entry["confidence"], reverse=True)
    return scored_candidates[:top_k]


def _rerank(query: str, candidates: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
    if not candidates:
        return []
    try:
        from sentence_transformers import CrossEncoder  # type: ignore

        model = CrossEncoder(SETTINGS.cross_encoder_model)
        pairs = [(query, record.get("simplified_text") or record_text(record)) for record in candidates]
        scores = model.predict(pairs)
        scored_candidates = []
        for record, raw_score in zip(candidates, scores):
            confidence = 1.0 / (1.0 + math.exp(-float(raw_score)))
            item = dict(record)
            item["confidence"] = confidence
            item["reranker_score"] = float(raw_score)
            scored_candidates.append(item)
        scored_candidates.sort(key=lambda entry: entry["confidence"], reverse=True)
        return scored_candidates[:top_k]
    except Exception:
        return _manual_rerank(query, candidates, top_k)


def retrieve(query: str) -> list[dict[str, Any]]:
    query = query.strip()
    if not query:
        return []
    dense = _build_dense_candidates(query, top_k=20)
    bm25 = _build_bm25_candidates(query, top_k=20)
    merged = _rrf_merge(dense, bm25)
    top = _rerank(query, merged[:30], top_k=5)
    results: list[dict[str, Any]] = []
    for rank, item in enumerate(top, start=1):
        result = dict(item)
        result["rank"] = rank
        result["source_label"] = make_source_label(result)
        result.setdefault("confidence", 0.0)
        results.append(result)
    return results
