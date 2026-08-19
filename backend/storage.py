from pathlib import Path
from uuid import uuid4
from fastapi import UploadFile
from backend.config import get_settings

class LocalStorage:
    """MVP file storage; route code only calls this class, so cloud storage can replace it later."""
    def save(self, folder: str, filename: str, content: bytes) -> str:
        root = get_settings().storage_root / folder; root.mkdir(parents=True, exist_ok=True)
        safe_name = f"{uuid4().hex}_{Path(filename).name}"
        path = root / safe_name; path.write_bytes(content)
        return str(path)

storage = LocalStorage()
