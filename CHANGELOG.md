# Changelog

## v0.4.0

### Added

- Phase 7 — AI Agents & MCP
  - `app.mcp.tools` (resume_search, interview_start, interview_answer, interview_get, follow_up_hint) + `TOOL_REGISTRY`
  - `app.mcp.server` (FastMCP when `mcp` installed, stdio fallback; `python -m app.mcp.server`)
  - `GET /mcp/tools` + `POST /mcp/call` REST bridge (`app.api.mcp`)
  - `app.agents.interview_agent` LangGraph agent orchestrating via MCP tools; `POST /agent/interview/start` + `POST /agent/interview/answer` (`app.api.agents`)
- Phase 8 — Auth & Security
  - `app.models.user` (users table), `user_id` FK on `interview_sessions`
  - `app.core.security` (pbkdf2, PyJWT `HS256`, `REQUIRE_AUTH` flag, `get_current_user_optional`)
  - `app.services.auth_service` + `POST /auth/register`, `POST /auth/login`, `GET /auth/me` (`app.api.auth`)
  - Interview routes optionally tied to authenticated user (ownership check when `user_id` set); CORS enabled
  - `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` in `app.core.settings` + `.env.example`
- Phase 9 — Streamlit
  - `frontend/app.py` (upload, auth login/register, start, answer, history, score, MCP explorer; `BACKEND_URL` env)
  - `frontend/requirements.txt` + `frontend/Dockerfile`
- Phase 10 — Deployment
  - `Dockerfile` (backend), `docker-compose.yml` (api + streamlit, optional ollama), `.dockerignore`
- Tests for auth/MCP/agent (`backend/tests/test_auth_and_mcp.py`)

### Fixed

- `InterviewHistoryEntry` now `score` + `score_delta` Optional for backward compat (`app.schemas.interview:45`)
- `interview_service` fallback: `first_question` never null (`_fallback_first_question`), normalized 0–10 scoring (`_normalize_score`), concise follow-up prefers answer topic
- `ask_question` + `submit_answer` now store both `score` and `score_delta`; `get_interview_session` normalizes legacy entries
- `Base.metadata` now includes `users` via `app.models` import; `init_db` + `conftest` load all models

### Changed

- `README` marks all Phases 1–10 complete; added architecture + run + Docker docs
- `requirements.txt` adds `streamlit`, `requests`, `PyJWT`

## v0.3.0

### Added

- AI Interviewer Flow via LangGraph (`app.rag.interview_graph`)
  - Generate opening interview question from the resume
  - LLM rubric evaluation of candidate answers (0-10) with strengths/weaknesses/feedback
  - Adaptive follow-up question generation
- `POST /interview/answer` endpoint
- `POST /interview/start` now returns the first generated question
- `current_question` column on `interview_sessions`
- Heuristic evaluation + template follow-up as offline fallback when the LLM is unavailable
- Test suite for the interview flow (`backend/tests/test_interview_flow.py`)

### Changed

- Session score is now the rounded average of per-answer scores (0-10)
- History entries record per-answer `score` and evaluation feedback

## v0.2.1

### Changed

- `.env` files are now loaded via python-dotenv in `app.core.settings`
- README updated to reflect actual LangChain/LangGraph integration status

### Removed

- Dead scaffold endpoints (`/test`, `/users/{user_id}`) and `User` schema
- Superseded `langchain_pipeline.py` (replaced by LangGraph pipeline)
- Scratch scripts with import-time side effects (`rag/test_rag.py`, `rag/test_pdf_loader.py`, `services/db_test.py`)
- Unused `LLM_PROVIDER` setting
- ChromaDB binaries and resume uploads removed from git tracking (now gitignored)

### Fixed

- RAG pipeline test now works with the LangGraph path active
- Shared `conftest.py` for tests; repo-root `pytest.ini` restricts collection to `backend/tests`

## v0.2.0

### Added

- Resume Upload API
- PDF Loader
- ChromaDB Persistent Storage
- Resume Ingestion Pipeline
- Ollama Integration

## v0.1.0

### Added

- FastAPI Project Setup
- PostgreSQL
- SQLAlchemy