"""Language detection module using FastText."""
from __future__ import annotations

import logging
from functools import lru_cache

from app.ai.config import SETTINGS

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_fasttext_model():
    """Load the FastText language ID model."""
    import fasttext  # type: ignore

    try:
        model = fasttext.load_model(str(SETTINGS.fasttext_langid_model))
        logger.info("Loaded FastText model from %s", SETTINGS.fasttext_langid_model)
        return model
    except Exception as e:
        logger.warning("Failed to load FastText model: %s", e)
        return None


def detect_language(text: str) -> str:
    """Detect the language code of the given text (e.g., 'en', 'hi', 'ta').

    Falls back to 'en' if detection fails or model is unavailable.
    """
    if not text or not text.strip():
        return "en"

    model = _load_fasttext_model()
    if not model:
        return "en"

    try:
        # FastText expects single line text
        clean_text = text.replace("\n", " ").strip()
        predictions = model.predict(clean_text, k=1)
        label = predictions[0][0]
        # Label format is '__label__en'
        lang_code = label.replace("__label__", "")
        return lang_code
    except Exception as e:
        logger.warning("Language detection failed: %s", e)
        return "en"
