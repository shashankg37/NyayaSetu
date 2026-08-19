from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent
BM25_PATH = BACKEND_ROOT / "data" / "indexes" / "bm25.pkl"


class Settings(BaseSettings):
    project_name: str = "Nyaya Setu API"
    env: str = "development"
    api_v1_str: str = "/api/v1"
    database_url: str = "sqlite:///./nyaya_setu.db"
    secret_key: str
    access_token_expire_minutes: int = 45
    refresh_token_expire_days: int = 7
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    max_upload_bytes: int = 10 * 1024 * 1024
    rate_limit_per_minute: int = 60
    storage_root: Path = Path("storage")

    qdrant_collection: str = "nyaya_setu_chunks"
    qdrant_url: str = "http://localhost:6333"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    confidence_threshold: float = 0.5
    evidence_min_chunks: int = 1
    evidence_min_agreement: int = 0
    evidence_min_authority: int = 0
    evidence_coverage_min: float = 0.2

    llm_provider: str = "hf"
    llm_model: str = "Qwen/Qwen2.5-7B-Instruct"
    hf_api_url: str = "https://router.huggingface.co/hf-inference/models"
    hf_api_key: str = ""
    vision_provider: str = "hf"
    vision_model: str = "Qwen/Qwen2.5-VL-7B-Instruct"
    gemini_model: str = "gemini-1.5-flash"
    gemini_api_key: str = ""

    working_language: str = "en"
    fasttext_langid_model: str = "lid.176.ftz"

    bhashini_api_url: str = ""
    bhashini_api_key: str = ""
    bhashini_user_id: str = ""
    bhashini_pipeline_id: str = ""
    bhashini_stt_service_id: str = ""
    bhashini_tts_service_id: str = ""
    bhashini_translate_url: str = ""
    bhashini_target_lang: str = "en"
    bhashini_timeout_seconds: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def fasttext_model_paths(self) -> list[Path]:
        configured = Path(self.fasttext_langid_model)
        return [
            configured,
            BACKEND_ROOT / configured,
            BACKEND_ROOT / "data" / "language_models" / configured.name,
            BACKEND_ROOT / "data" / "language_models" / "lid.176.ftz",
            Path("data/language_models/lid.176.ftz"),
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


class _SettingsProxy:
    def __getattr__(self, name: str):
        return getattr(get_settings(), name)


SETTINGS = _SettingsProxy()
