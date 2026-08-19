"""Local pickle persistence for the BM25 index."""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any


def save_pickle(payload: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL))


def load_pickle(path: Path) -> Any:
    return pickle.loads(path.read_bytes())
