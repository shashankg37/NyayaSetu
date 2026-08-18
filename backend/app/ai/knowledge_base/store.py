from __future__ import annotations

import json
import pickle
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.ai.config import BM25_PATH, CORPUS_PATH, KB_DIR, SAMPLE_CORPUS_PATH


@dataclass
class ChunkRecord:
    chunk_id: str
    source: str
    act: str
    section: str
    topic: str
    original_text: str
    simplified_text: str
    source_url: str = ""
    page: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def ensure_kb_dirs() -> None:
    KB_DIR.mkdir(parents=True, exist_ok=True)


def load_json_records(path: Path = CORPUS_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def save_json_records(records: list[dict[str, Any]], path: Path = CORPUS_PATH) -> None:
    ensure_kb_dirs()
    path.write_text(json.dumps(records, indent=2, ensure_ascii=True), encoding="utf-8")


def load_seed_records() -> list[dict[str, Any]]:
    if SAMPLE_CORPUS_PATH.exists():
        return json.loads(SAMPLE_CORPUS_PATH.read_text(encoding="utf-8"))
    return []


def save_pickle(obj: Any, path: Path = BM25_PATH) -> None:
    ensure_kb_dirs()
    with path.open("wb") as handle:
        pickle.dump(obj, handle)


def load_pickle(path: Path = BM25_PATH) -> Any | None:
    if not path.exists():
        return None
    with path.open("rb") as handle:
        return pickle.load(handle)


def normalize_key(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def record_text(record: dict[str, Any]) -> str:
    pieces = [
        record.get("act", ""),
        record.get("section", ""),
        record.get("topic", ""),
        record.get("original_text", ""),
        record.get("simplified_text", ""),
    ]
    return " ".join(piece for piece in pieces if piece).strip()


def make_source_label(record: dict[str, Any]) -> str:
    act = record.get("act") or "Unknown source"
    section = record.get("section")
    if section:
        return f"{act} - {section}"
    return act

