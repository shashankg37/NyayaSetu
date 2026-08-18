from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


# Load environment variables from root .env if it exists
try:
    from dotenv import load_dotenv
    root_env = Path(__file__).resolve().parent.parent / ".env"
    if root_env.exists():
        load_dotenv(root_env)
except ImportError:
    pass


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
KB_DIR = DATA_DIR / "knowledge_base"
QDRANT_DIR = DATA_DIR / "qdrant"
TEMPLATES_DIR = ROOT_DIR / "app" / "templates" / "drafts"
SAMPLE_CORPUS_PATH = KB_DIR / "sample_sources.json"
CORPUS_PATH = KB_DIR / "corpus.json"
BM25_PATH = KB_DIR / "bm25.pkl"


@dataclass(frozen=True)
class Settings:
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "nyaya_setu_chunks")
    embedding_model: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    cross_encoder_model: str = os.getenv(
        "CROSS_ENCODER_MODEL", "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
    )
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    working_language: str = os.getenv("WORKING_LANGUAGE", "en")
    fasttext_langid_model: str = os.getenv(
        "FASTTEXT_LANGID_MODEL", str(DATA_DIR / "language_models" / "lid.176.ftz")
    )
    bhashini_api_url: str = os.getenv("BHASHINI_API_URL", "")
    bhashini_api_key: str = os.getenv("BHASHINI_API_KEY", "")
    bhashini_translate_url: str = os.getenv("BHASHINI_TRANSLATE_URL", "")
    bhashini_target_lang: str = os.getenv("BHASHINI_TARGET_LANG", "en")


SETTINGS = Settings()
