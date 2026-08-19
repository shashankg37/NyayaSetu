"""AI stubs — internal helpers still used by services and graph.

speech and vision have been promoted to app/ai/speech.py and app/ai/vision.py.
"""
from app.ai.ai_stubs.draft_fields import missing_fields
from app.ai.ai_stubs.generation import generate_answer
from app.ai.ai_stubs.intent import classify_intent
from app.ai.ai_stubs.retrieval import retrieve
