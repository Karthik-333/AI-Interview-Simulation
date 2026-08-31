# Copilot Instructions for AI Interview Simulation

## Build, test, and lint

- Install dependencies: `pip install -r requirements.txt`
- Run API locally: `uvicorn backend.app.main:app --reload`
- Initialize database: `python backend/app/init_db.py`
- Run tests: `pytest backend/tests -q`
- Run a single test: `pytest backend/tests/test_interview_service.py -q` (or any one test module)
- Existing RAG script checks still exist:
  - `python backend/app/rag/test_pdf_loader.py`
  - `python backend/app/rag/test_rag.py`

## Architecture

- FastAPI exposes resume upload and interview/session routes.
- Resume uploads are saved to `backend/uploads`, then ingested into ChromaDB through the RAG pipeline.
- The answer path is: query embedding -> LangGraph retrieval -> prompt building -> Ollama response, with fallback shims if optional packages are missing.
- SQLAlchemy persists interview sessions, including history and score.
- LangGraph is the orchestration layer for retrieval and generation, while services keep interview business logic.

## Key conventions

- Keep API routes thin and place logic in `backend/app/services`.
- Keep RAG concerns split across loader, chunker, embedding, vector store, prompt, LLM, and graph modules.
- Reuse `backend/app/core/settings.py` for path, model, and database constants.
- Preserve current API behavior while replacing internals incrementally.
- Prefer session-aware interview logic: session start should return an id, ask flow should attach history, and session retrieval should expose persisted state.
- Use ChromaDB collection `resume_chunks` for stored resume content.

## Current migration direction

- LangChain/LangGraph migration is in place; future work should focus on stronger scoring rules, better follow-up question generation, and product-facing session/history APIs.
