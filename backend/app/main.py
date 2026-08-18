import logging, time
from collections import defaultdict, deque
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.api.v1 import auth, documents, draft, query, timeline, users
from app.core.config import get_settings
from app.db import Base, engine
import app.models  # registers models before create_all

settings = get_settings(); logger = logging.getLogger(__name__)
app = FastAPI(title=settings.project_name, version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
_requests: dict[str, deque[float]] = defaultdict(deque)

@app.middleware('http')
async def rate_limit(request: Request, call_next):
    if request.url.path in {f'{settings.api_v1_str}/auth/register', f'{settings.api_v1_str}/auth/login', f'{settings.api_v1_str}/health'}:
        now = time.monotonic(); bucket = _requests[request.client.host if request.client else 'unknown']
        while bucket and bucket[0] < now - 60: bucket.popleft()
        if len(bucket) >= settings.rate_limit_per_minute: return JSONResponse({'detail': 'Too many requests. Please try again shortly.'}, 429)
        bucket.append(now)
    return await call_next(request)

@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    logger.exception('Unhandled request error')
    return JSONResponse(status_code=500, content={'detail': 'An unexpected server error occurred.'})

@app.on_event('startup')
def startup() -> None:
    # Useful for a first MVP run; Alembic supplies the same schema in deployed environments.
    Base.metadata.create_all(bind=engine)

@app.get(f'{settings.api_v1_str}/health', tags=['system'])
def health():
    with engine.connect() as connection: connection.execute(text('SELECT 1'))
    return {'status': 'ok', 'version': app.version}

for router in (auth.router, users.router, query.router, documents.router, draft.router, timeline.router): app.include_router(router, prefix=settings.api_v1_str)
