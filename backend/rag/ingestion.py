"""Document loaders for legal source files (PDF, HTML, TXT, JSON)."""
from __future__ import annotations

import json
import logging
import math
import re
import uuid
from dataclasses import dataclass, field
from functools import lru_cache
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

import logging
import torch
import torch.nn.functional as F
from functools import lru_cache
from typing import Any
from transformers import AutoTokenizer, AutoModel

logger = logging.getLogger(__name__)

# Strict taxonomy as requested
LEGAL_DOMAINS = [
    "labour",
    "consumer",
    "women_and_children",
    "disability",
    "senior_citizens",
    "property",
    "criminal",
    "civil",
    "government_services",
    "legal_aid",
    "general_rights",
]

# Descriptive phrases used to form prototype embeddings
DOMAIN_DESCRIPTIONS = {
    "labour": "Employment, wages, workplace disputes, employer, worker, labour rights, unions.",
    "consumer": "Consumer complaints, defective products, refund, deficiency in service, buyer, seller.",
    "women_and_children": "Women's rights, domestic violence, child custody, maintenance, juvenile justice.",
    "disability": "Rights of persons with disabilities, accessibility, discrimination against disabled.",
    "senior_citizens": "Senior citizens, elderly care, maintenance of parents.",
    "property": "Property disputes, land acquisition, real estate, inheritance, tenancy, eviction.",
    "criminal": "Criminal offenses, FIR, bail, police, arrest, theft, fraud, violence.",
    "civil": "Civil disputes, contracts, injunctions, general civil matters.",
    "government_services": "RTI, government schemes, pensions, public grievances, welfare.",
    "legal_aid": "Free legal aid, NALSA, DLSA, lok adalat, legal representation.",
    "general_rights": "Fundamental rights, constitutional issues, general human rights.",
}

# The model path
MODEL_NAME = "law-ai/InLegalBERT"

TOPIC_BY_DOMAIN = {
    "labour": "wages_and_employment",
    "consumer": "consumer_protection",
    "women_and_children": "protection_and_maintenance",
    "disability": "accessibility_and_non_discrimination",
    "senior_citizens": "maintenance_and_welfare",
    "property": "tenancy_and_property",
    "criminal": "offences_and_procedure",
    "civil": "civil_procedure",
    "government_services": "public_services_and_rti",
    "legal_aid": "legal_services",
    "general_rights": "fundamental_rights",
}

BENEFICIARY_BY_DOMAIN = {
    "labour": "worker",
    "consumer": "consumer",
    "women_and_children": "woman_or_child",
    "disability": "person_with_disability",
    "senior_citizens": "senior_citizen",
    "property": "property_holder_or_tenant",
    "criminal": "accused_or_victim",
    "civil": "party_to_dispute",
    "government_services": "citizen",
    "legal_aid": "legal_aid_seeker",
    "general_rights": "citizen",
}


def _topic_and_beneficiary(domain: str, text: str) -> tuple[str, str]:
    lowered = (text or "").lower()
    topic = TOPIC_BY_DOMAIN.get(domain, "unknown")
    beneficiary = BENEFICIARY_BY_DOMAIN.get(domain, "unknown")
    if "daily wage" in lowered or "daily-wage" in lowered:
        beneficiary = "daily_wage_worker"
        topic = "wages_and_employment"
    if "tenant" in lowered or "landlord" in lowered or "deposit" in lowered:
        topic = "tenancy_and_deposit"
        beneficiary = "tenant"
    if "rti" in lowered:
        topic = "right_to_information"
        beneficiary = "citizen"
    return topic, beneficiary

@lru_cache(maxsize=1)
def _get_device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")

@lru_cache(maxsize=1)
def _load_inlegalbert():
    """Load the tokenizer and model for InLegalBERT."""
    try:
        device = _get_device()
        logger.info(f"Loading InLegalBERT on {device}...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModel.from_pretrained(MODEL_NAME).to(device)
        model.eval()
        return tokenizer, model
    except Exception as e:
        logger.error("Failed to load InLegalBERT: %s", e)
        return None, None

def _mean_pooling(model_output, attention_mask):
    """Mean Pooling - Take attention mask into account for correct averaging."""
    token_embeddings = model_output[0] # First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

@lru_cache(maxsize=1)
def _get_domain_prototypes() -> dict[str, torch.Tensor]:
    """Precompute normalized embeddings for the legal domains."""
    tokenizer, model = _load_inlegalbert()
    if not model or not tokenizer:
        return {}
    
    device = _get_device()
    prototypes = {}
    
    with torch.no_grad():
        for domain, desc in DOMAIN_DESCRIPTIONS.items():
            encoded_input = tokenizer(desc, padding=True, truncation=True, return_tensors='pt').to(device)
            model_output = model(**encoded_input)
            embedding = _mean_pooling(model_output, encoded_input['attention_mask'])
            normalized_emb = F.normalize(embedding, p=2, dim=1)
            prototypes[domain] = normalized_emb.cpu()
            
    return prototypes

def classify_text(text: str) -> dict[str, Any]:
    """Single-text classification fallback/wrapper."""
    results = classify_batch([text])
    return results[0]

def classify_batch(texts: list[str]) -> list[dict[str, Any]]:
    """Classify multiple texts using batching for performance."""
    results = []
    default_result = {
        "legal_domain": "unknown",
        "topic": "unknown",
        "beneficiary": "unknown",
        "domain_confidence": 0.0,
        "topic_confidence": 0.0,
        "beneficiary_confidence": 0.0,
    }
    
    if not texts:
        return results
        
    tokenizer, model = _load_inlegalbert()
    if not model or not tokenizer:
        logger.warning("InLegalBERT not loaded, falling back to 'unknown'.")
        return [default_result.copy() for _ in texts]
        
    prototypes = _get_domain_prototypes()
    if not prototypes:
        return [default_result.copy() for _ in texts]
        
    # Stack prototypes into a single tensor [num_domains, hidden_size]
    domain_names = list(prototypes.keys())
    proto_tensor = torch.cat([prototypes[d] for d in domain_names], dim=0)
    
    device = _get_device()
    batch_size = 8
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        # Truncate text to max 512 tokens
        encoded_input = tokenizer(
            batch_texts, 
            padding=True, 
            truncation=True, 
            max_length=512, 
            return_tensors='pt'
        ).to(device)
        
        with torch.no_grad():
            model_output = model(**encoded_input)
            batch_embeddings = _mean_pooling(model_output, encoded_input['attention_mask'])
            batch_normalized = F.normalize(batch_embeddings, p=2, dim=1).cpu()
            
            # Compute cosine similarity: [batch_size, hidden_size] @ [hidden_size, num_domains] -> [batch_size, num_domains]
            similarities = torch.matmul(batch_normalized, proto_tensor.T)
            
            # Get max similarity
            max_scores, max_idxs = torch.max(similarities, dim=1)
            
            for text, score, idx in zip(batch_texts, max_scores, max_idxs):
                score_val = score.item()
                domain = domain_names[idx.item()]
                topic, beneficiary = _topic_and_beneficiary(domain, text)
                if score_val < 0.2:
                    domain = "unknown"
                    topic = "unknown"
                    beneficiary = "unknown"
                results.append({
                    "legal_domain": domain,
                    "topic": topic,
                    "beneficiary": beneficiary,
                    "domain_confidence": score_val,
                    "topic_confidence": score_val if domain != "unknown" else 0.0,
                    "beneficiary_confidence": score_val if domain != "unknown" else 0.0,
                })
                
    return results
"""Metadata enrichment for legal chunks.

Combines loader metadata, classifier tags, and chunk provenance
into the final metadata structure stored alongside each chunk.
"""

from typing import Any




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
        "topic": classification.get("topic", "unknown"),
        "legal_domain": classification.get("legal_domain", "unknown"),
        "beneficiary": classification.get("beneficiary", "unknown"),
        "jurisdiction": (extra or {}).get("jurisdiction") or chunk.metadata.get("jurisdiction") or "unknown",
        "act": chunk.source or chunk.document_name,
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
            if value in (None, ""):
                continue
            if key not in metadata or metadata.get(key) in (None, "", "unknown"):
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

import logging
import re
import uuid
from typing import Any

from backend.config import BM25_PATH, SETTINGS
from backend.rag.store import save_pickle

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

        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, str(record.get("chunk_id") or idx)))
        points.append(
            rest.PointStruct(
                id=point_id,
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
