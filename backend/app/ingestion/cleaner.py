"""Text cleaning utilities for legal documents."""
from __future__ import annotations

import re


# Patterns for common page headers/footers in Indian legal PDFs
_PAGE_NUM_RE = re.compile(r"^\s*-?\s*\d+\s*-?\s*$", re.MULTILINE)
_HEADER_RE = re.compile(
    r"^\s*(THE GAZETTE OF INDIA|MINISTRY OF LAW|GOVERNMENT OF INDIA|"
    r"OFFICIAL GAZETTE|EXTRAORDINARY|PART [IVX]+)\s*$",
    re.MULTILINE | re.IGNORECASE,
)
_MULTIPLE_NEWLINES_RE = re.compile(r"\n{3,}")
_MULTIPLE_SPACES_RE = re.compile(r"[ \t]{2,}")
_UNICODE_DASH_RE = re.compile(r"[\u2013\u2014\u2015]")
_SMART_QUOTES_RE = re.compile(r"[\u201c\u201d\u201e\u201f]")
_SINGLE_SMART_RE = re.compile(r"[\u2018\u2019\u201a\u201b]")


def clean_text(text: str) -> str:
    """Clean raw extracted text while preserving legal formatting.

    Removes:
    - Standalone page numbers
    - Common gazette/government PDF headers
    - Excessive whitespace
    - Smart quotes and special dashes

    Preserves:
    - Section numbering (e.g. '5.', '(a)', '(i)')
    - Clause markers
    - Legal formatting
    """
    if not text:
        return ""

    # Normalize unicode characters
    text = _UNICODE_DASH_RE.sub("-", text)
    text = _SMART_QUOTES_RE.sub('"', text)
    text = _SINGLE_SMART_RE.sub("'", text)

    # Remove standalone page numbers
    text = _PAGE_NUM_RE.sub("", text)

    # Remove gazette/government headers
    text = _HEADER_RE.sub("", text)

    # Normalize whitespace
    text = _MULTIPLE_SPACES_RE.sub(" ", text)
    text = _MULTIPLE_NEWLINES_RE.sub("\n\n", text)

    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()


def clean_page(page_text: str) -> str:
    """Clean a single page of text."""
    return clean_text(page_text)


def clean_pages(pages: list[str]) -> list[str]:
    """Clean a list of page texts, dropping empty pages."""
    cleaned = [clean_page(page) for page in pages]
    return [page for page in cleaned if page]
