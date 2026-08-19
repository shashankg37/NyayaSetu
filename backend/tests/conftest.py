import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-nyaya-setu-tests-32ch")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_nyaya_setu.db")
os.environ.setdefault("LLM_PROVIDER", "local")
os.environ.setdefault("HF_API_KEY", "")
os.environ.setdefault("BHASHINI_API_KEY", "")
os.environ.setdefault("BHASHINI_API_URL", "")

from backend.config import get_settings

get_settings.cache_clear()
