# Nyaya Setu

Nyaya Setu is a FastAPI and LangGraph backend for a multilingual legal-awareness MVP. The core loop is: understand the citizen's message, retrieve verified legal material, explain it simply, and suggest a safe next action.

## Architecture

The active application lives in `backend/`. It keeps one deployable backend process with these pieces:

- FastAPI routers in `backend/app/api/v1`
- SQLAlchemy models for structured PostgreSQL data
- LangGraph flow in `backend/app/ai/graph.py`
- Hybrid legal retrieval in `backend/app/ai/ai_stubs/retrieval.py`
- Provider-configurable answer generation in `backend/app/ai/llm.py`
- Manual knowledge ingestion in `backend/scripts/ingest.py`

The MVP knowledge base is limited to official legal-awareness material and primary official legal sources such as India Code, Acts, Rules, Regulations, e-Gazette, NALSA, and SLSA material.

## Features

- JWT authentication and password hashing
- Text legal questions with grounded responses
- Turn-based voice query support through Bhashini when configured
- Uploaded document extraction with multimodal provider boundary and deterministic fallback
- Conversational drafting field collection and PDF/DOCX generation
- Qdrant semantic retrieval plus BM25 keyword retrieval
- Reciprocal Rank Fusion and cross-encoder reranking
- Evidence-based confidence gate with legal-aid fallback

## Setup

```bash
cd backend
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

API docs are available at `http://localhost:8000/docs`.

## Knowledge Base

Place official PDF, HTML, TXT, or JSON source files under `backend/data/source_docs/`, then run:

```bash
cd backend
python scripts/ingest.py
```

The ingestion script extracts text, chunks it, enriches metadata, embeds chunks with multilingual MiniLM, indexes Qdrant, and rebuilds BM25. The original legal text remains authoritative; simplified text is only an explanation aid.

## Environment

Important variables:

- `DATABASE_URL`: PostgreSQL URL for app data
- `SECRET_KEY`: JWT signing secret
- `QDRANT_URL` and `QDRANT_COLLECTION`: vector retrieval configuration
- `EMBEDDING_MODEL`: multilingual Sentence Transformers model
- `CROSS_ENCODER_MODEL`: reranker model
- `LLM_PROVIDER`: `hf`, `gemini`, or `local`
- `LLM_MODEL`: Qwen model name for the Hugging Face route
- `HF_API_KEY`: Hugging Face token for Qwen inference
- `GEMINI_API_KEY`: optional fallback
- `BHASHINI_API_URL`, `BHASHINI_API_KEY`, `BHASHINI_TRANSLATE_URL`: voice and translation integration
- `FASTTEXT_LANGID_MODEL`: local FastText language ID model path
- `CONFIDENCE_THRESHOLD`: evidence gate threshold

## Docker

```bash
docker-compose up --build
```

This starts the backend with PostgreSQL and Qdrant according to the compose files.

## Testing

```bash
cd backend
pytest
```

The tests cover auth, health, query, document upload, drafting, timeline behavior, and AI wiring. External providers can be left unconfigured for local tests; deterministic fallbacks keep the API available.

## Limitations

Nyaya Setu is legal-awareness software, not a lawyer. It does not provide exhaustive legal research, it does not work fully offline for new AI requests, and low-confidence evidence paths deliberately route users toward legal aid or more information.

## Legal Disclaimer

Responses are educational and grounded in the available source corpus. Users should verify legal steps with official authorities, legal-aid services, or a qualified lawyer before acting.
