from pathlib import Path
import sqlite3
from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from backend.config import get_settings

settings = get_settings()
engine_kwargs = {"connect_args": {"check_same_thread": False}} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def ensure_sqlite_schema() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    parsed = urlparse(settings.database_url)
    db_path = parsed.path
    if not db_path:
        return

    sqlite_file = Path(db_path)
    if sqlite_file.as_posix().startswith('/./'):
        sqlite_file = Path(sqlite_file.as_posix()[3:])

    if not sqlite_file.is_absolute():
        sqlite_file = (Path.cwd() / sqlite_file).resolve()

    if not sqlite_file.exists():
        return

    with sqlite3.connect(sqlite_file) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(users)").fetchall()}
        missing = [
            ("full_name", "TEXT"),
            ("phone", "TEXT"),
            ("city", "TEXT"),
            ("issue_type", "TEXT"),
        ]
        for column_name, column_type in missing:
            if column_name not in columns:
                connection.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                connection.commit()


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
