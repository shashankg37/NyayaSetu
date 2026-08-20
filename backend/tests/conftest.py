import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-nyaya-setu-tests-32ch")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_nyaya_setu.db")
os.environ.setdefault("LLM_PROVIDER", "hf")
os.environ.setdefault("LLM_MODEL", "Qwen/Qwen3.5-27B")
os.environ.setdefault("HF_API_KEY", os.environ.get("HF_API_KEY", ""))
os.environ.setdefault("BHASHINI_API_KEY", "")
os.environ.setdefault("BHASHINI_API_URL", "")

from backend.config import get_settings

get_settings.cache_clear()
