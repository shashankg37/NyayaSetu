"""Rule-based safety checks. LLM is not used as the safety source of truth."""
from __future__ import annotations

from typing import Any

UNSAFE_MARKERS = (
    "how to make a bomb",
    "buy a gun to kill",
    "commit suicide method",
    "hack aadhaar",
    "forge court order",
    "bribe the judge",
)
EMERGENCY_MARKERS = (
    "i want to die",
    "kill myself",
    "suicide",
    "being raped",
    "domestic violence now",
    "police are beating",
    "child is missing",
)


def check_safety(text: str) -> dict[str, Any]:
    lowered = (text or "").lower()
    if not lowered.strip():
        return {"safe": True, "reason": "", "status": "ok"}
    if any(marker in lowered for marker in UNSAFE_MARKERS):
        return {
            "safe": False,
            "reason": "The request asks for assistance with an illegal or harmful act.",
            "status": "unsafe",
        }
    if any(marker in lowered for marker in EMERGENCY_MARKERS):
        return {
            "safe": True,
            "reason": "Possible emergency or high-risk situation.",
            "status": "emergency",
        }
    return {"safe": True, "reason": "", "status": "ok"}
