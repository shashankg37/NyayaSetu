# Nyaya Setu Backend

This is the production-oriented SIH MVP backend. It keeps the existing FastAPI API contracts and adds the in-repo AI layer under `app/ai`.

## Request Flow

Text, voice, or document input enters a FastAPI router, is stored through the service layer, then moves through the LangGraph pipeline:

`input processing -> intent -> hybrid retrieval -> evidence gate -> provider generation -> response`

Hybrid retrieval uses Qdrant for semantic search, BM25 for exact legal terms, Reciprocal Rank Fusion for merging, and a sentence-transformers cross-encoder for reranking.

## Run Locally

```bash
pip install -r requirements.txt
copy .env.example .env
uvicorn backend.main:app --reload
```

Open `http://localhost:8000/docs`.

## Build The Knowledge Base

```bash
python scripts/ingest.py
```

Add official source files to `data/source_docs/` before running ingestion. The script builds the local processed corpus, Qdrant vectors, and BM25 index.

## Docker

```bash
docker-compose up --build
```

Docker uses PostgreSQL for structured data and Qdrant for vector retrieval.

## Test

```bash
pytest
```

The local test suite uses SQLite and provider fallbacks so it can run without real API keys.

## Current Boundaries

The MVP includes official-source RAG, document extraction, voice transcription hooks, drafting, auth, and safe fallback behavior. New AI requests require connectivity and configured providers.
