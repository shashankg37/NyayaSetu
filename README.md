# Nyaya Setu AI scaffold

This repository now contains the AI-only side of the Nyaya Setu prompt:

- `app/ai_stubs/retrieval.py` uses LangChain documents, HuggingFace embeddings, BM25 retrieval, and Qdrant-backed dense retrieval with RRF and reranking.
- `app/ai_stubs/generation.py` uses LangChain prompts and structured JSON parsing for grounded answers, while keeping the confidence gate ahead of Gemini calls.
- `app/ai_stubs/vision.py` extracts fields from uploaded legal documents and feeds the extracted text back into retrieval.
- `app/ai_stubs/speech.py` transcribes audio through Bhashini/Dhruva when configured, with local fallbacks.
- `app/ai_stubs/intent.py` classifies the user intent.
- `app/ai_stubs/draft_fields.py` checks draft templates for missing fields.
- `app/graph.py` wires the steps together with LangGraph when the package is installed.
- `scripts/ingest.py` builds the knowledge base and local Qdrant/BM25 indexes.

## Quick start

1. Put source documents in `data/source_docs/` or use the bundled seed corpus.
2. Run `python scripts/ingest.py` to build the local index.
3. Call `app.graph.run_pipeline(...)` for text, audio, or image flows.

## Notes

- The external AI services are optional and configured through environment variables.
- If LangChain integrations, Gemini, Qdrant, or Bhashini are not available, the code falls back to deterministic local behavior so the pipeline still works in a demo environment.
