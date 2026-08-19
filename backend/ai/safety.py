"""Safety and content moderation checks."""
from __future__ import annotations

import logging
from typing import Any

from backend.ai.llm import get_provider

logger = logging.getLogger(__name__)


def check_safety(text: str) -> dict[str, Any]:
    """Check if the text violates safety policies (self-harm, violence, hate speech).
    
    Returns a dict with 'safe' (bool) and 'reason' (str).
    """
    if not text or not text.strip():
        return {"safe": True, "reason": ""}

    provider = get_provider()
    prompt = (
        f"Analyze the following text for safety violations (self-harm, violence, hate speech, illegal acts).\n"
        f"Text: \"{text}\"\n\n"
        f"Respond with a JSON object containing two keys: 'safe' (boolean) and 'reason' (string explaining why if unsafe, or empty string if safe)."
    )

    try:
        # Use low temperature for consistent evaluation
        result = provider.generate_json(prompt, temperature=0.0)
        if result is None:
            # If the provider fails, default to safe but log a warning
            logger.warning("Safety check failed to generate JSON, defaulting to safe.")
            return {"safe": True, "reason": ""}
            
        safe = result.get("safe", True)
        reason = result.get("reason", "")
        
        # Coerce to bool in case model returned string "true"/"false"
        if isinstance(safe, str):
            safe = safe.lower() == "true"
            
        return {"safe": safe, "reason": reason}
    except Exception as e:
        logger.error("Safety check encountered an error: %s", e)
        # Default to safe if the check fails, to avoid blocking legitimate requests
        return {"safe": True, "reason": ""}
