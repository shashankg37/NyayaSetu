# Nyaya Setu backend

This is the compact, demo-ready backend for Nyaya Setu. It provides accounts, safe file handling, legal-document drafts, and the API contracts the future AI layer will use.

## How a request moves

A request enters a router in `app/api/v1`. Pydantic checks its shape. The router calls one matching service file, which stores the necessary record and calls a clearly-labelled function in `app/ai_stubs` when AI is needed. The service returns a typed response. The stubs are deliberately realistic mock data, not retrieval, Gemini, OCR, speech, or LangGraph implementations.

For a draft, the flow is real: the backend stores answers, checks required fields, writes both PDF and DOCX, and makes the PDF downloadable. It never invents missing information.

## Run

Copy `.env.example` to `.env`, replace `SECRET_KEY`, then run:

```bash
docker-compose up --build
```

Open `http://localhost:8000/docs`. For a local Python run, set `SECRET_KEY`, install `requirements.txt`, then use `uvicorn app.main:app --reload`.

## Test

```bash
pytest
```

The test suite uses SQLite only for isolated local tests. Docker uses PostgreSQL, and the migration uses PostgreSQL JSONB fields. Self-registration always creates a `citizen`; the admin-only role endpoint is the only role-change path.
