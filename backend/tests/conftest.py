import os

from dotenv import load_dotenv

from backend.config import BACKEND_ROOT, REPO_ROOT

load_dotenv(BACKEND_ROOT / ".env", override=False)
load_dotenv(REPO_ROOT / ".env", override=False)

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-nyaya-setu-tests-32ch")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_nyaya_setu.db")
os.environ.setdefault("LLM_PROVIDER", "hf")
os.environ.setdefault("LLM_MODEL", "Qwen/Qwen3.5-27B")
os.environ.setdefault("SARVAM_API_KEY", "")
os.environ.setdefault("SARVAM_STT_MODEL", "saaras:v3")
os.environ.setdefault("SARVAM_TTS_MODEL", "bulbul:v3")
os.environ.setdefault("SARVAM_DEFAULT_LANGUAGE", "en-IN")
os.environ.setdefault("SARVAM_TTS_SPEAKER", "shubh")

from backend.config import get_settings

get_settings.cache_clear()
