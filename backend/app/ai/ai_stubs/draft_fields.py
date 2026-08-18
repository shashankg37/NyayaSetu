from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from app.ai.config import TEMPLATES_DIR
from app.ai.knowledge_base.store import normalize_key


def _load_template(doc_type: str) -> dict[str, Any] | None:
    target = normalize_key(doc_type)
    if not TEMPLATES_DIR.exists():
        return None
    for path in TEMPLATES_DIR.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if normalize_key(str(payload.get("doc_type", path.stem))) == target:
            return payload
    return None


def _field_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def missing_fields(doc_type: str, known_fields: dict) -> list[str]:
    """Given a document type and what's already been provided, returns the list of
    required fields still missing."""
    template = _load_template(doc_type)
    if not template:
        return []
    required_fields = template.get("required_fields", [])
    normalized_known = {normalize_key(str(key)): value for key, value in known_fields.items()}
    missing: list[str] = []
    for field in required_fields:
        if not _field_present(normalized_known.get(normalize_key(field))):
            missing.append(field)
    return missing

