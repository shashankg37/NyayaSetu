"""Document loaders for legal source files (PDF, HTML, TXT, JSON)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RawDocument:
    """A loaded document with its text and metadata."""
    document_id: str
    document_name: str
    source: str
    source_url: str
    text: str
    pages: list[str] = field(default_factory=list)
    file_type: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def load_pdf(path: Path) -> RawDocument | None:
    """Load a PDF file, extracting text per page."""
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        return None
    try:
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n\n".join(pages)
        if not text.strip():
            return None
        return RawDocument(
            document_id=path.stem,
            document_name=path.name,
            source=path.stem,
            source_url=path.as_uri(),
            text=text,
            pages=pages,
            file_type="pdf",
        )
    except Exception:
        return None


def load_html(path: Path) -> RawDocument | None:
    """Load an HTML file, extracting visible text."""
    try:
        from bs4 import BeautifulSoup  # type: ignore
    except ImportError:
        return None
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(raw, "html.parser")
        # Remove script/style tags
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(" ", strip=True)
        if not text.strip():
            return None
        return RawDocument(
            document_id=path.stem,
            document_name=path.name,
            source=path.stem,
            source_url=path.as_uri(),
            text=text,
            pages=[text],
            file_type="html",
        )
    except Exception:
        return None


def load_txt(path: Path) -> RawDocument | None:
    """Load a plain text file."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if not text.strip():
            return None
        return RawDocument(
            document_id=path.stem,
            document_name=path.name,
            source=path.stem,
            source_url=path.as_uri(),
            text=text,
            pages=[text],
            file_type="txt",
        )
    except Exception:
        return None


def load_json(path: Path) -> RawDocument | None:
    """Load a JSON file containing legal records.

    Supports both list-of-dicts (each record becomes a paragraph)
    and single-dict formats.
    """
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

    if isinstance(payload, list):
        paragraphs: list[str] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            parts = [str(v) for v in item.values() if isinstance(v, (str, int, float)) and str(v).strip()]
            if parts:
                paragraphs.append(" ".join(parts))
        text = "\n\n".join(paragraphs)
    elif isinstance(payload, dict):
        parts = [str(v) for v in payload.values() if isinstance(v, (str, int, float)) and str(v).strip()]
        text = " ".join(parts)
    else:
        return None

    if not text.strip():
        return None
    return RawDocument(
        document_id=path.stem,
        document_name=path.name,
        source=path.stem,
        source_url=path.as_uri(),
        text=text,
        pages=[text],
        file_type="json",
    )


_LOADERS = {
    ".pdf": load_pdf,
    ".html": load_html,
    ".htm": load_html,
    ".txt": load_txt,
    ".json": load_json,
}


def load_file(path: Path) -> RawDocument | None:
    """Load a file using the appropriate loader based on extension."""
    loader = _LOADERS.get(path.suffix.lower())
    if loader is None:
        return None
    return loader(path)


def load_directory(directory: Path) -> list[RawDocument]:
    """Recursively load all supported files from a directory."""
    documents: list[RawDocument] = []
    if not directory.exists():
        return documents
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        doc = load_file(path)
        if doc is not None:
            documents.append(doc)
    return documents
