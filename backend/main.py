import logging
import time
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.api import auth, chat, documents, drafting, lawyers, research, users, voice, speech
from backend.config import get_settings
from backend.database import Base, ensure_sqlite_schema, engine
import backend.models.database  # noqa: F401

settings = get_settings()
logger = logging.getLogger(__name__)
app = FastAPI(title=settings.project_name, version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
_requests: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.url.path.rstrip("/") == f"{settings.api_v1_str}/health":
        return await call_next(request)
    now = time.monotonic()
    bucket = _requests[request.client.host if request.client else "unknown"]
    while bucket and bucket[0] < now - 60:
        bucket.popleft()
    if len(bucket) >= settings.rate_limit_per_minute:
        return JSONResponse({"detail": "Too many requests. Please try again shortly."}, 429)
    bucket.append(now)
    return await call_next(request)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    logger.exception("Unhandled request error")
    return JSONResponse(status_code=500, content={"detail": "An unexpected server error occurred."})


@app.on_event("startup")
def startup() -> None:
    ensure_sqlite_schema()
    Base.metadata.create_all(bind=engine)


@app.get(f"{settings.api_v1_str}/health", tags=["system"])
def health():
    qdrant_ok = False
    try:
        from qdrant_client import QdrantClient  # type: ignore

        client = QdrantClient(url=settings.qdrant_url, timeout=3)
        client.get_collections()
        qdrant_ok = True
    except Exception:
        qdrant_ok = False
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "version": app.version,
        "database": "ok",
        "qdrant": "ok" if qdrant_ok else "unavailable",
    }


app.include_router(auth.router, prefix=settings.api_v1_str)
app.include_router(users.router, prefix=settings.api_v1_str)
app.include_router(documents.router, prefix=settings.api_v1_str)
app.include_router(drafting.router, prefix=settings.api_v1_str)
app.include_router(chat.router, prefix=f"{settings.api_v1_str}/chat")
app.include_router(voice.router, prefix=f"{settings.api_v1_str}/voice")
app.include_router(speech.router, prefix=f"{settings.api_v1_str}/speech")
app.include_router(research.router, prefix=settings.api_v1_str)
app.include_router(lawyers.router, prefix=settings.api_v1_str)
