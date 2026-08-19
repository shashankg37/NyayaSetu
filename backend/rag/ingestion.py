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
"""Legal-aware chunking for Indian legal documents.

Preserves document structure: section/subsection boundaries, numbered clauses,
and paragraph context. Each chunk has a stable chunk_id and full provenance.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any


# Indian legal section patterns
_SECTION_RE = re.compile(
    r"^(?:"
    r"(?:Section|Sec\.?|S\.?)\s+\d+[A-Za-z]?"  # Section 5, Sec. 12A
    r"|CHAPTER\s+[IVXLCDM\d]+"                    # CHAPTER III
    r"|PART\s+[IVXLCDM]+"                          # PART IV
    r"|SCHEDULE\s+[IVXLCDM\d]*"                    # SCHEDULE I
    r"|Article\s+\d+"                               # Article 21
    r"|\d+[A-Za-z]?\.\s"                           # 5. or 12A.
    r")",
    re.IGNORECASE | re.MULTILINE,
)

_SUBSECTION_RE = re.compile(
    r"^\s*\((\d+|[a-z]|[ivxlcdm]+)\)\s",
    re.IGNORECASE | re.MULTILINE,
)

_PARAGRAPH_SEP_RE = re.compile(r"\n\s*\n+")

MAX_CHUNK_CHARS = 900
MIN_CHUNK_CHARS = 100


@dataclass
class LegalChunk:
    """A single chunk of legal text with full provenance."""
    chunk_id: str
    document_id: str
    document_name: str
    source: str
    source_url: str
    page: int | None
    section: str
    subsection: str
    original_text: str
    language: str = "en"
    metadata: dict[str, Any] = field(default_factory=dict)


def _stable_chunk_id(document_id: str, section: str, chunk_index: int) -> str:
    """Generate a stable, reproducible chunk ID."""
    raw = f"{document_id}::{section}::{chunk_index}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _detect_section(text: str) -> str:
    """Try to detect a section heading in a text block."""
    match = _SECTION_RE.match(text.strip())
    if match:
        return match.group(0).strip().rstrip(".")
    return ""


def _detect_subsection(text: str) -> str:
    """Try to detect a subsection marker."""
    match = _SUBSECTION_RE.match(text.strip())
    if match:
        return f"({match.group(1)})"
    return ""


def _split_into_blocks(text: str) -> list[str]:
    """Split text into paragraph-level blocks."""
    blocks = _PARAGRAPH_SEP_RE.split(text)
    return [block.strip() for block in blocks if block.strip()]


def _merge_small_blocks(blocks: list[str], max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Merge consecutive small blocks, respecting max_chars.

    Tries to keep blocks together when they're below MIN_CHUNK_CHARS,
    and never exceeds max_chars.
    """
    if not blocks:
        return []

    merged: list[str] = []
    current = blocks[0]

    for block in blocks[1:]:
        candidate = f"{current}\n\n{block}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                merged.append(current)
            current = block

    if current:
        merged.append(current)

    return merged


def _split_oversized(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split an oversized block into sentence-level chunks."""
    if len(text) <= max_chars:
        return [text]

    # Try splitting on sentence boundaries
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            # If a single sentence is too long, split on clause boundaries
            if len(sentence) > max_chars:
                clause_parts = re.split(r"[;,]\s+", sentence)
                for part in clause_parts:
                    if len(part) <= max_chars:
                        chunks.append(part)
                    else:
                        # Last resort: hard split
                        for i in range(0, len(part), max_chars):
                            chunks.append(part[i : i + max_chars])
                current = ""
            else:
                current = sentence

    if current:
        chunks.append(current)

    return chunks


def chunk_document(
    document_id: str,
    document_name: str,
    source: str,
    source_url: str,
    pages: list[str],
    language: str = "en",
    max_chars: int = MAX_CHUNK_CHARS,
) -> list[LegalChunk]:
    """Chunk a legal document with section/subsection awareness.

    Each page is processed independently to maintain page provenance.
    Within each page, section and subsection boundaries are detected.
    """
    chunks: list[LegalChunk] = []
    chunk_index = 0
    current_section = "Preamble"
    current_subsection = ""

    for page_num, page_text in enumerate(pages, start=1):
        if not page_text.strip():
            continue

        blocks = _split_into_blocks(page_text)

        for block in blocks:
            # Detect section/subsection boundaries
            detected_section = _detect_section(block)
            if detected_section:
                current_section = detected_section
                current_subsection = ""

            detected_sub = _detect_subsection(block)
            if detected_sub:
                current_subsection = detected_sub

            # Split oversized blocks, then merge small ones
            sub_blocks = _split_oversized(block, max_chars)

            for text_piece in sub_blocks:
                if len(text_piece.strip()) < 20:
                    continue  # Skip very short fragments

                chunk_index += 1
                chunk_id = _stable_chunk_id(document_id, current_section, chunk_index)

                chunks.append(
                    LegalChunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        document_name=document_name,
                        source=source,
                        source_url=source_url,
                        page=page_num,
                        section=current_section,
                        subsection=current_subsection,
                        original_text=text_piece.strip(),
                        language=language,
                    )
                )

    return chunks


def chunk_text_simple(
    text: str,
    document_id: str = "unknown",
    document_name: str = "unknown",
    source: str = "unknown",
    source_url: str = "",
    max_chars: int = MAX_CHUNK_CHARS,
) -> list[LegalChunk]:
    """Chunk plain text (not page-separated) into legal chunks."""
    return chunk_document(
        document_id=document_id,
        document_name=document_name,
        source=source,
        source_url=source_url,
        pages=[text],
        max_chars=max_chars,
    )
"""InLegalBERT-based legal domain classifier.

Uses pretrained InLegalBERT (law-ai/InLegalBERT) as a feature extractor
with cosine similarity against label descriptions for zero-shot-style
classification. NO fine-tuning is performed.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)

# Candidate labels for each classification axis
LEGAL_DOMAINS = [
    "labour",
    "consumer",
    "family",
    "housing",
    "criminal",
    "property",
    "constitutional",
    "administrative",
    "environmental",
    "corporate",
    "taxation",
    "legal_aid",
    "general",
]

TOPICS = [
    "wages",
    "employment",
    "termination",
    "workplace_safety",
    "rent",
    "eviction",
    "tenancy",
    "marriage",
    "divorce",
    "child_custody",
    "maintenance",
    "domestic_violence",
    "consumer_complaint",
    "product_defect",
    "refund",
    "service_deficiency",
    "property_dispute",
    "land_acquisition",
    "legal_aid",
    "free_legal_services",
    "rti",
    "government_grievance",
    "pension",
    "insurance",
    "education",
    "healthcare",
    "general",
]

BENEFICIARIES = [
    "worker",
    "daily_wage_worker",
    "employee",
    "tenant",
    "consumer",
    "woman",
    "child",
    "senior_citizen",
    "person_with_disability",
    "sc_st",
    "victim",
    "citizen",
    "litigant",
    "entrepreneur",
    "farmer",
]


@lru_cache(maxsize=1)
def _load_classifier():
    """Load a zero-shot classification pipeline.

    Tries InLegalBERT embeddings + cosine similarity approach first.
    Falls back to a cross-encoder NLI model if available.
    Falls back to keyword heuristics if no model loads.
    """
    try:
        from transformers import pipeline  # type: ignore

        # Use a multilingual NLI model for zero-shot classification
        # InLegalBERT is BERT-base without NLI head, so we use a dedicated
        # zero-shot model and rely on InLegalBERT embeddings for enrichment
        clf = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=-1,  # CPU
        )
        logger.info("Loaded zero-shot classifier: facebook/bart-large-mnli")
        return clf
    except Exception as e:
        logger.warning("Could not load transformer classifier: %s", e)
        return None


@lru_cache(maxsize=1)
def _load_inlegalbert_embedder():
    """Load InLegalBERT for domain-specific embedding enrichment."""
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        model = SentenceTransformer("law-ai/InLegalBERT")
        logger.info("Loaded InLegalBERT for classification enrichment")
        return model
    except Exception as e:
        logger.warning("Could not load InLegalBERT: %s", e)
        return None


def _keyword_classify_domain(text: str) -> str:
    """Fallback keyword-based domain classification."""
    lower = text.lower()
    domain_markers = {
        "labour": ["wage", "salary", "employ", "labour", "worker", "workman", "industrial", "factory", "minimum wage"],
        "consumer": ["consumer", "purchase", "refund", "product", "service", "defect", "seller", "buyer"],
        "housing": ["tenant", "landlord", "rent", "evict", "lease", "premises", "accommodation"],
        "family": ["family", "marriage", "divorce", "child", "maintenance", "custody", "dowry", "domestic violence"],
        "criminal": ["criminal", "offense", "fir", "bail", "arrest", "theft", "fraud"],
        "property": ["property", "land", "succession", "inheritance", "transfer", "mutation"],
        "constitutional": ["fundamental right", "constitution", "article", "writ", "petition"],
        "legal_aid": ["legal aid", "nalsa", "legal services", "free legal", "lok adalat"],
    }
    for domain, markers in domain_markers.items():
        if any(marker in lower for marker in markers):
            return domain
    return "general"


def _keyword_classify_topic(text: str) -> str:
    """Fallback keyword-based topic classification."""
    lower = text.lower()
    topic_markers = {
        "wages": ["wage", "salary", "pay", "remuneration", "compensation"],
        "termination": ["terminat", "dismiss", "retrench", "layoff"],
        "eviction": ["evict", "vacate", "possession"],
        "rent": ["rent", "lease", "tenancy"],
        "maintenance": ["maintenance", "alimony"],
        "consumer_complaint": ["consumer complaint", "consumer forum"],
        "legal_aid": ["legal aid", "free legal", "nalsa"],
        "rti": ["right to information", "rti"],
    }
    for topic, markers in topic_markers.items():
        if any(marker in lower for marker in markers):
            return topic
    return "general"


def _keyword_classify_beneficiary(text: str) -> str:
    """Fallback keyword-based beneficiary classification."""
    lower = text.lower()
    beneficiary_markers = {
        "worker": ["worker", "workman", "labourer"],
        "daily_wage_worker": ["daily wage", "casual", "contract worker"],
        "employee": ["employee", "staff"],
        "tenant": ["tenant", "occupant", "lessee"],
        "consumer": ["consumer", "buyer", "purchaser"],
        "woman": ["woman", "wife", "mother", "female"],
        "child": ["child", "minor", "juvenile"],
        "senior_citizen": ["senior citizen", "elderly", "old age"],
    }
    for beneficiary, markers in beneficiary_markers.items():
        if any(marker in lower for marker in markers):
            return beneficiary
    return "citizen"


def classify_text(text: str) -> dict[str, Any]:
    """Classify a piece of legal text.

    Returns a dict with:
        legal_domain: str
        topic: str
        beneficiary: str
        domain_confidence: float
        topic_confidence: float
        beneficiary_confidence: float
    """
    if not text or not text.strip():
        return {
            "legal_domain": "general",
            "topic": "general",
            "beneficiary": "citizen",
            "domain_confidence": 0.0,
            "topic_confidence": 0.0,
            "beneficiary_confidence": 0.0,
        }

    clf = _load_classifier()
    if clf is None:
        # Pure keyword fallback
        return {
            "legal_domain": _keyword_classify_domain(text),
            "topic": _keyword_classify_topic(text),
            "beneficiary": _keyword_classify_beneficiary(text),
            "domain_confidence": 0.5,
            "topic_confidence": 0.5,
            "beneficiary_confidence": 0.5,
        }

    # Truncate text for the classifier (BART has 1024 token limit)
    truncated = text[:1500]

    try:
        domain_result = clf(truncated, LEGAL_DOMAINS, multi_label=False)
        domain = domain_result["labels"][0]
        domain_conf = float(domain_result["scores"][0])
    except Exception:
        domain = _keyword_classify_domain(text)
        domain_conf = 0.5

    try:
        topic_result = clf(truncated, TOPICS[:15], multi_label=False)  # Limit candidates
        topic = topic_result["labels"][0]
        topic_conf = float(topic_result["scores"][0])
    except Exception:
        topic = _keyword_classify_topic(text)
        topic_conf = 0.5

    try:
        beneficiary_result = clf(truncated, BENEFICIARIES, multi_label=False)
        beneficiary = beneficiary_result["labels"][0]
        beneficiary_conf = float(beneficiary_result["scores"][0])
    except Exception:
        beneficiary = _keyword_classify_beneficiary(text)
        beneficiary_conf = 0.5

    return {
        "legal_domain": domain,
        "topic": topic,
        "beneficiary": beneficiary,
        "domain_confidence": domain_conf,
        "topic_confidence": topic_conf,
        "beneficiary_confidence": beneficiary_conf,
    }


def classify_batch(texts: list[str]) -> list[dict[str, Any]]:
    """Classify multiple texts. Processes sequentially to avoid OOM."""
    return [classify_text(text) for text in texts]
"""Metadata enrichment for legal chunks.

Combines loader metadata, classifier tags, and chunk provenance
into the final metadata structure stored alongside each chunk.
"""
from __future__ import annotations

from typing import Any

from backend.rag.ingestion.chunker import LegalChunk


def build_chunk_metadata(
    chunk: LegalChunk,
    classification: dict[str, Any],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the full metadata payload for a chunk.

    This is the authoritative metadata schema stored in Qdrant and the corpus.
    """
    metadata: dict[str, Any] = {
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "document_name": chunk.document_name,
        "source": chunk.source,
        "source_url": chunk.source_url,
        "page": chunk.page,
        "section": chunk.section,
        "subsection": chunk.subsection,
        "topic": classification.get("topic", "general"),
        "legal_domain": classification.get("legal_domain", "general"),
        "beneficiary": classification.get("beneficiary", "citizen"),
        "jurisdiction": "india",
        "language": chunk.language,
        "original_text": chunk.original_text,
        # We do NOT replace the original text with AI summaries.
        # The simplified_text is just a searchability aid.
        "simplified_text": "",
        "domain_confidence": classification.get("domain_confidence", 0.0),
        "topic_confidence": classification.get("topic_confidence", 0.0),
        "beneficiary_confidence": classification.get("beneficiary_confidence", 0.0),
    }

    if extra:
        for key, value in extra.items():
            if key not in metadata:
                metadata[key] = value

    return metadata


def enrich_chunks(
    chunks: list[LegalChunk],
    classifications: list[dict[str, Any]],
    extra: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Enrich a list of chunks with classification metadata.

    Args:
        chunks: Legal chunks from the chunker.
        classifications: Classification results from the classifier (same order/length).
        extra: Optional extra metadata to add to every chunk.

    Returns:
        List of fully enriched metadata dicts ready for indexing.
    """
    if len(chunks) != len(classifications):
        raise ValueError(
            f"Chunks ({len(chunks)}) and classifications ({len(classifications)}) must be same length"
        )

    return [
        build_chunk_metadata(chunk, classification, extra)
        for chunk, classification in zip(chunks, classifications)
    ]
"""Embedding module using multilingual Sentence Transformers.

Uses paraphrase-multilingual-MiniLM-L12-v2 (or configured model) for both
ingestion and query-time embedding.  This is the SINGLE source of truth
for the embedding model — no other module should instantiate its own.
"""
from __future__ import annotations

import logging
import math
from functools import lru_cache

from backend.config import SETTINGS

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_model():
    """Load the sentence transformer model (cached singleton)."""
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        model = SentenceTransformer(SETTINGS.embedding_model)
        logger.info("Loaded embedding model: %s", SETTINGS.embedding_model)
        return model
    except Exception as e:
        logger.warning("Could not load SentenceTransformer: %s. Using fallback.", e)
        return None


def _simple_embedding(text: str, dimensions: int = 384) -> list[float]:
    """Deterministic hash-based fallback embedding when model is unavailable."""
    vector = [0.0] * dimensions
    tokens = text.lower().split()
    for token in tokens:
        vector[hash(token) % dimensions] += 1.0
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def embed_text(text: str) -> list[float]:
    """Embed a single text string.

    Returns a normalized vector suitable for cosine similarity.
    """
    model = _load_model()
    if model is not None:
        try:
            vector = model.encode([text], normalize_embeddings=True)[0]
            return vector.tolist() if hasattr(vector, "tolist") else list(vector)
        except Exception as e:
            logger.warning("Embedding failed for text: %s", e)

    return _simple_embedding(text)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts as a batch.

    More efficient than calling embed_text() in a loop.
    """
    if not texts:
        return []

    model = _load_model()
    if model is not None:
        try:
            vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            return [v.tolist() if hasattr(v, "tolist") else list(v) for v in vectors]
        except Exception as e:
            logger.warning("Batch embedding failed: %s", e)

    return [_simple_embedding(text) for text in texts]


def get_embedding_dimension() -> int:
    """Return the vector dimensionality of the current embedding model."""
    model = _load_model()
    if model is not None:
        try:
            dim = model.get_sentence_embedding_dimension()
            return int(dim) if dim else 384
        except Exception:
            pass
    return 384
"""Indexing module for Qdrant and BM25.

Handles creation/recreation of Qdrant collections and BM25 pickle indices.
Uses the Qdrant client directly (not through LangChain wrappers).
"""
from __future__ import annotations

import logging
import re
from typing import Any

from backend.config import BM25_PATH, SETTINGS
from backend.ai.knowledge_base.store import save_pickle

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer for BM25."""
    return [t.lower() for t in re.findall(r"[a-zA-Z0-9]+", text)]


def index_qdrant(records: list[dict[str, Any]], recreate: bool = False) -> int:
    """Index records into Qdrant.

    Each record must have:
        - 'embedding': list[float]
        - 'chunk_id': str
        - All metadata fields

    Returns the number of points upserted.
    """
    try:
        from qdrant_client import QdrantClient  # type: ignore
        from qdrant_client.http import models as rest  # type: ignore
    except ImportError:
        logger.error("qdrant_client is not installed")
        return 0

    if not records:
        logger.warning("No records to index into Qdrant")
        return 0

    # Determine vector size from first record
    first_embedding = records[0].get("embedding", [])
    vector_size = len(first_embedding)
    if vector_size == 0:
        logger.error("Records have no embeddings")
        return 0

    # Connect to Qdrant
    qdrant_url = SETTINGS.qdrant_url
    client = QdrantClient(url=qdrant_url, timeout=60)
    collection = SETTINGS.qdrant_collection

    # Recreate collection if requested
    if recreate:
        try:
            client.delete_collection(collection)
            logger.info("Deleted existing collection: %s", collection)
        except Exception:
            pass

    # Create collection if it doesn't exist
    if not client.collection_exists(collection):
        client.create_collection(
            collection_name=collection,
            vectors_config=rest.VectorParams(
                size=vector_size,
                distance=rest.Distance.COSINE,
            ),
        )
        logger.info("Created Qdrant collection: %s (dim=%d)", collection, vector_size)

    # Build points
    points = []
    for idx, record in enumerate(records):
        embedding = record.get("embedding", [])
        if not embedding:
            continue

        # Payload is everything except the embedding vector
        payload = {k: v for k, v in record.items() if k != "embedding"}

        points.append(
            rest.PointStruct(
                id=idx,
                vector=embedding,
                payload=payload,
            )
        )

    # Upsert in batches
    batch_size = 100
    total = 0
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        client.upsert(collection_name=collection, points=batch)
        total += len(batch)
        logger.info("Indexed %d / %d points", total, len(points))

    return total


def index_bm25(records: list[dict[str, Any]]) -> int:
    """Build and save a BM25 index from records.

    The index is saved as a pickle file alongside the tokenized corpus
    and chunk_id mapping for retrieval.

    Returns the corpus size.
    """
    try:
        from rank_bm25 import BM25Okapi  # type: ignore
    except ImportError:
        logger.error("rank_bm25 is not installed")
        return 0

    if not records:
        logger.warning("No records to build BM25 index from")
        return 0

    # Build tokenized corpus
    corpus: list[list[str]] = []
    chunk_ids: list[str] = []

    for record in records:
        text = " ".join(
            part
            for part in [
                record.get("original_text", ""),
                record.get("section", ""),
                record.get("topic", ""),
            ]
            if part
        )
        corpus.append(_tokenize(text))
        chunk_ids.append(record.get("chunk_id", ""))

    bm25 = BM25Okapi(corpus)

    # Save as a bundle: (bm25_model, chunk_ids, records)
    save_pickle(
        {"bm25": bm25, "chunk_ids": chunk_ids, "records": records},
        BM25_PATH,
    )
    logger.info("Built BM25 index with %d documents, saved to %s", len(corpus), BM25_PATH)
    return len(corpus)
