"""Application configuration for NyayaSetu."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_ROOT.parent

BM25_PATH = BACKEND_ROOT / "data" / "indexes" / "bm25.pkl"


def _load_env_files() -> None:
    """Load backend/.env and repository-root .env.

    Existing environment variables take precedence.
    """
    for env_path in (
        BACKEND_ROOT / ".env",
        REPO_ROOT / ".env",
    ):
        if env_path.is_file():
            load_dotenv(env_path, override=False)


_load_env_files()


class Settings(BaseSettings):

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    project_name: str = "Nyaya Setu API"
    env: str = "development"
    api_v1_str: str = "/api/v1"

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    database_url: str = "sqlite:///./nyaya_setu.db"

    # Authentication
    secret_key: str
    access_token_expire_minutes: int = 45
    refresh_token_expire_days: int = 7

    # ------------------------------------------------------------------
    # API / Security
    # ------------------------------------------------------------------
    cors_origins: str = (
        "http://localhost:3000,"
        "http://localhost:5173"
    )

    max_upload_bytes: int = 10 * 1024 * 1024
    rate_limit_per_minute: int = 60

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------
    storage_root: Path = Path("storage")

    # ------------------------------------------------------------------
    # Qdrant
    # ------------------------------------------------------------------
    qdrant_collection: str = "nyaya_setu_chunks"
    qdrant_url: str = "http://localhost:6333"

    # ------------------------------------------------------------------
    # Embeddings / Retrieval
    # ------------------------------------------------------------------
    embedding_model: str = (
        "sentence-transformers/"
        "paraphrase-multilingual-MiniLM-L12-v2"
    )

    inlegalbert_model: str = "law-ai/InLegalBERT"

    cross_encoder_model: str = (
        "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
    )

    # ------------------------------------------------------------------
    # Evidence Gate
    # ------------------------------------------------------------------
    confidence_threshold: float = 0.5
    evidence_min_chunks: int = 1
    evidence_min_agreement: int = 0
    evidence_min_authority: int = 0
    evidence_coverage_min: float = 0.2

    # ------------------------------------------------------------------
    # Primary LLM — Groq
    # ------------------------------------------------------------------
    llm_provider: str = "groq"

    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3.6-27b"

    llm_model: str = "qwen/qwen3.6-27b"

    # ------------------------------------------------------------------
    # Legacy Hugging Face fallback
    # ------------------------------------------------------------------
    hf_provider: str = "featherless-ai"

    hf_api_url: str = (
        "https://router.huggingface.co/"
        "hf-inference/models"
    )

    hf_api_key: str = ""

    # ------------------------------------------------------------------
    # Optional Gemini fallback
    # ------------------------------------------------------------------
    gemini_model: str = "gemini-1.5-flash"
    gemini_api_key: str = ""

    # ------------------------------------------------------------------
    # Language
    # ------------------------------------------------------------------
    working_language: str = "en"


    # ------------------------------------------------------------------
    # Sarvam AI
    # ------------------------------------------------------------------
    sarvam_api_key: str = ""

    sarvam_base_url: str = "https://api.sarvam.ai"

    sarvam_stt_model: str = "saaras:v3"

    sarvam_tts_model: str = "bulbul:v3"

    sarvam_default_language: str = "en-IN"

    sarvam_tts_speaker: str = "shubh"

    sarvam_timeout_seconds: int = 60

    # ------------------------------------------------------------------
    # Pydantic Settings
    # ------------------------------------------------------------------
    model_config = SettingsConfigDict(
        env_file=(
            str(BACKEND_ROOT / ".env"),
            str(REPO_ROOT / ".env"),
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]




@lru_cache
def get_settings() -> Settings:
    return Settings()


class _SettingsProxy:
    def __getattr__(self, name: str):
        return getattr(get_settings(), name)


SETTINGS = _SettingsProxy()
