# Nyaya Setu — AI & Backend Integration

This repository contains **one integrated system**: a FastAPI backend that uses the Nyaya Setu AI package (in-process) to provide legal assistance to citizens.

## Architecture Overview

```
backend/                    ← FastAPI application (public API)
  app/
    ai_stubs/               ← These import from nyaya_setu_ai package
    api/                    ← HTTP routers
    core/                   ← FastAPI config
    services/               ← Business logic
    models/                 ← Database models
    
app/                        ← AI Package (nyaya_setu_ai)
  ai_stubs/                 ← Individual AI services (retrieval, generation, etc.)
  graph.py                  ← LangGraph pipeline + clean entry points
  knowledge_base/           ← Local vector + BM25 indexes
  templates/                ← Legal document templates
  config.py                 ← AI settings
  types.py                  ← Data structures
```

**Key insight**: The backend imports and calls the AI package directly (like any Python library), not over HTTP. One process, one `docker-compose up`.

## Setup

### 1. Install Dependencies

```bash
# Install backend + AI package + all deps in one step
cd backend
pip install -r requirements.txt
```

This automatically installs the AI package (`app/`) in editable mode (via `-e ../app` in `requirements.txt`).

### 2. Configure Environment

Copy the root `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required keys:
- `GEMINI_API_KEY` — for answer generation (Google Gemini API)
- `QDRANT_URL` — where Qdrant vector database runs (default: `http://localhost:6333`)
- `DATABASE_URL` — Postgres for backend data (default: `sqlite` for dev/testing)
- `SECRET_KEY` — JWT signing key for auth

Both the AI package and the backend read from the same `.env` file.

### 3. Build the Knowledge Base (one time, or after adding new documents)

```bash
python scripts/ingest.py
```

This:
- Reads documents from `app/data/source_docs/`
- Builds Qdrant vector index
- Builds local BM25 index
- Stores in `app/data/qdrant/` and `app/data/knowledge_base/`

### 4. Run External Services (Docker Compose)

```bash
docker-compose up -d
```

This starts:
- **Postgres** (backend data, migrations via Alembic)
- **Qdrant** (vector search for retrieval)
- **FastAPI backend** (with AI package built-in)

Alternatively, run just Qdrant and Postgres separately, then start the backend manually:

```bash
# Terminal 1: Start Postgres + Qdrant
docker-compose up postgres qdrant

# Terminal 2: Run the backend
cd backend
uvicorn app.main:app --reload
```

Then visit:
- API docs: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`

### 5. Run Tests

```bash
# Test the AI package alone
pytest tests/

# Test the backend
cd backend
pytest tests/

# Test the wiring (proves backend → AI package is connected)
pytest tests/test_wiring.py -v
```

## How the Wiring Works

### Backend Calls the AI Package

Each backend API endpoint eventually calls an AI function. For example, `POST /api/v1/query`:

```
POST /api/v1/query (with {"text": "..."})
  ↓
backend/app/api/query_router.py (HTTP handler)
  ↓
backend/app/services/query_service.py (business logic)
  ↓
backend/app/ai_stubs/retrieval.py (thin wrapper)
  ↓
from nyaya_setu_ai.ai_stubs.retrieval import retrieve
  ↓
Real retrieval: vector search + BM25 + reranking
  ↓
Result: list of relevant legal passages
  ↓
backend/app/ai_stubs/generation.py (thin wrapper)
  ↓
from nyaya_setu_ai.ai_stubs.generation import generate_answer
  ↓
Real generation: Gemini API (grounded with citations)
  ↓
Return: {"your_right": "...", "what_law_says": "...", ...}
```

### Clean Entry Points in the AI Package

The AI package provides simple entry points that the backend calls:

```python
# In app/graph.py (AI package)

def run_query_pipeline(query: str, input_type: str = "text") -> dict:
    """Full pipeline: intent → retrieve → generate. Returns plain dict."""
    
def run_query_pipeline_with_audio(audio_bytes: bytes) -> dict:
    """Pipeline starting from audio transcription."""
    
def run_query_pipeline_with_document(file_bytes: bytes) -> dict:
    """Pipeline starting from document extraction."""
    
def get_missing_fields(doc_type: str, known_fields: dict) -> list[str]:
    """Draft field completion."""
```

The backend's AI stubs are just thin wrappers around these:

```python
# In backend/app/ai_stubs/retrieval.py

from nyaya_setu_ai.ai_stubs.retrieval import retrieve as ai_retrieve

def retrieve(query: str) -> list[dict]:
    """Backend function. Calls the real AI package."""
    return ai_retrieve(query)  # ← That's it!
```

### Error Handling

If the AI service fails (e.g., Qdrant down, Gemini quota exceeded), the wrapper catches it and returns sensible fallbacks so the backend stays online:

```python
def retrieve(query: str) -> list[dict]:
    try:
        return ai_retrieve(query)
    except Exception as e:
        print(f"Error: {e}")
        return []  # Empty results, not a crash
```

## Configuration

### AI Settings (`SETTINGS` in `app/config.py`)

Set these in `.env` to customize AI behavior:

```env
# Embedding model (HuggingFace)
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# Cross-encoder for reranking
CROSS_ENCODER_MODEL=cross-encoder/mmarco-mMiniLMv2-L12-H384-v1

# LLM
GEMINI_MODEL=gemini-1.5-flash
GEMINI_API_KEY=...

# Vector database
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=nyaya_setu_chunks

# Confidence threshold for refusing to answer
CONFIDENCE_THRESHOLD=0.5

# Language and translation (optional)
WORKING_LANGUAGE=en
BHASHINI_API_KEY=...  # For Indian language support
```

### Backend Settings (`Settings` in `backend/app/core/config.py`)

```env
# Database
DATABASE_URL=postgresql://user:password@host/dbname

# Auth
SECRET_KEY=<32+ random characters>
ACCESS_TOKEN_EXPIRE_MINUTES=45

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Folder Structure

```
.
├── .env                          ← Shared config (backend + AI)
├── .env.example                  ← Template (commit this, not .env)
├── pyproject.toml                ← AI package metadata
├── requirements.txt              ← AI package deps
├── scripts/
│   └── ingest.py                ← Build knowledge base
│
├── app/                          ← AI PACKAGE (nyaya_setu_ai)
│   ├── graph.py                  ← Entry points for backend
│   ├── config.py                 ← AI settings
│   ├── types.py                  ← PipelineState & return types
│   ├── ai_stubs/                 ← Core AI functions
│   │   ├── retrieval.py           ├─ Vector + BM25 search
│   │   ├── generation.py          ├─ Gemini-based answer
│   │   ├── intent.py              ├─ User intent classification
│   │   ├── vision.py              ├─ Document extraction
│   │   ├── speech.py              ├─ Audio transcription
│   │   └── draft_fields.py        └─ Template field completion
│   ├── knowledge_base/           ← Indexes (built by ingest.py)
│   │   ├── store.py               ├─ Vector DB client
│   │   └── sample_sources.json    └─ Seed documents
│   └── templates/                ← Legal document templates
│       └── drafts/
│
├── backend/                      ← FastAPI BACKEND
│   ├── app/
│   │   ├── main.py               ← FastAPI app setup
│   │   ├── db.py                 ← SQLAlchemy session
│   │   ├── core/
│   │   │   └── config.py          └─ Backend settings
│   │   ├── models/               ← SQLAlchemy ORM models
│   │   ├── schemas/              ← Pydantic request/response schemas
│   │   ├── services/             ← Business logic (queries, users, etc.)
│   │   ├── api/                  ← HTTP route handlers
│   │   └── ai_stubs/             ← Wrappers around AI package
│   │       ├── retrieval.py       ├─ Calls nyaya_setu_ai.ai_stubs.retrieval
│   │       ├── generation.py      ├─ Calls nyaya_setu_ai.ai_stubs.generation
│   │       ├── intent.py          ├─ Calls nyaya_setu_ai.ai_stubs.intent
│   │       ├── vision.py          ├─ Calls nyaya_setu_ai.ai_stubs.vision
│   │       ├── speech.py          ├─ Calls nyaya_setu_ai.ai_stubs.speech
│   │       └── draft_fields.py    └─ Calls nyaya_setu_ai.ai_stubs.draft_fields
│   ├── tests/
│   │   ├── test_query.py         ← Query endpoint tests
│   │   ├── test_auth.py          ← Auth tests
│   │   └── test_wiring.py        ← AI package integration tests
│   ├── requirements.txt          ← Includes "-e ../app" (AI package)
│   ├── Dockerfile                ← Docker build
│   └── README.md                 ← Backend-specific docs
│
├── tests/                        ← AI package tests
│   └── test_ai_pipeline.py
│
└── README.md                     ← This file
```

## Testing the Wiring

To verify the backend is actually calling the real AI package:

```bash
cd backend
pytest tests/test_wiring.py -v
```

Key tests:
- `test_backend_retrieval_calls_real_ai_package()` — Verifies `retrieve()` is wired
- `test_backend_generation_calls_real_ai_package()` — Verifies `generate_answer()` is wired
- `test_query_endpoint_uses_real_ai()` — End-to-end: API → backend → AI package

If these pass, the connection is proven.

## One-Sentence Explanation

*"The backend is one app, and it uses the AI logic the same way it would use any other Python library it depends on."*

## Deployment

### Docker Compose (Recommended for Development & Demo)

```bash
docker-compose up
```

Starts Postgres, Qdrant, and the FastAPI backend in one command.

### Docker (Production-like)

```bash
docker build -t nyaya-setu-backend:latest .
docker run --env-file .env --network host nyaya-setu-backend:latest
```

The `Dockerfile` automatically:
1. Installs all backend requirements (including the AI package via `-e ../app`)
2. Runs migrations
3. Starts the API

### Manual (Debugging)

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Troubleshooting

### `ModuleNotFoundError: No module named 'nyaya_setu_ai'`

The AI package wasn't installed. From `backend/`, run:

```bash
pip install -e ../app
```

Or reinstall backend deps:

```bash
pip install -r requirements.txt
```

### Qdrant connection refused

Make sure Qdrant is running:

```bash
docker-compose up qdrant  # or your own Qdrant instance
```

Check the `QDRANT_URL` in `.env` (default: `http://localhost:6333`).

### Gemini API key errors

Set a valid `GEMINI_API_KEY` in `.env`:

```bash
export GEMINI_API_KEY=<your-key>
# or add to .env:
GEMINI_API_KEY=your-key-here
```

### Backend returns mock data instead of real AI answers

This means the backend's AI stubs are still using old placeholder functions. Verify:

1. Backend installed the AI package: `pip show nyaya-setu-ai`
2. Backend's `ai_stubs/retrieval.py` imports from `nyaya_setu_ai`: `grep "from nyaya_setu_ai" backend/app/ai_stubs/retrieval.py`
3. Re-install: `pip install -e ./app --force-reinstall`

## Notes

- **Single process, not microservices**: The AI logic runs in the same Python process as the FastAPI backend. This is simpler to explain and debug than separate services.
- **Fallbacks**: If external services (Gemini, Qdrant, Bhashini) are unavailable, the pipeline returns sensible partial results or empty data rather than crashing.
- **Shared config**: Both the AI package and backend read from the same root `.env` file, so API keys and endpoints are defined once.
- **Editable install**: The AI package is installed with `pip install -e ../app`, so changes to `app/` are immediately reflected in the backend without reinstalling.
