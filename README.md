# AI Interview Simulation

An AI-powered interview simulation platform that generates personalized interview questions and answers based on the candidate's resume using Retrieval-Augmented Generation (RAG) and Large Language Models (LLMs).

---

## 🚀 Current Status

**Project Stage:** Phase 10 — Deployment (All Phases Complete)

### ✅ Completed

- FastAPI Backend + CORS
- SQLAlchemy ORM (SQLite default, PostgreSQL-ready via `DATABASE_URL`, `users` + `interview_sessions` with `user_id` FK)
- Resume PDF Processing + Upload API (`POST /resume/upload_resume`)
- Text Chunking, SentenceTransformer Embeddings (all-MiniLM-L6-v2), ChromaDB, Semantic Search
- Ollama Integration (Llama 3.2) with offline heuristic fallback
- RAG Ingestion Pipeline + LangChain Components + LangGraph RAG Pipeline (retrieve → compose → generate)
- LangGraph Interview Flow (`POST /interview/start` → `POST /interview/answer` → `GET /interview/session/{id}`; 0–10 avg scoring, adaptive follow-ups)
- AI Agents & MCP (`GET /mcp/tools`, `POST /mcp/call`, `POST /agent/interview/*`; `app.mcp` + `app.agents` via LangGraph)
- Auth & Security (`POST /auth/register`, `POST /auth/login`, `GET /auth/me`; JWT via PyJWT, pbkdf2, optional `REQUIRE_AUTH`)
- Streamlit Dashboard (`frontend/app.py`: upload, auth, start, answer, history, score; `BACKEND_URL` env)
- Deployment (`Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`, `.dockerignore`)

## 📈 Development Progress

- ✅ Phase 1 — Backend Foundations
- ✅ Phase 2 — Database & Architecture
- ✅ Phase 3 — Build RAG From Scratch
- ✅ Phase 4 — Production AI Backend
- ✅ Phase 5 — LangChain
- ✅ Phase 6 — LangGraph
- ✅ Phase 7 — AI Agents & MCP
- ✅ Phase 8 — Auth, Security, Login
- ✅ Phase 9 — Streamlit
- ✅ Phase 10 — Deployment

### 📅 Planned (next)

- PostgreSQL Migration (prod)
- MLflow Experiment Tracking
- Observability / Rate Limiting
- E2E Tests & CI

---

## 🏗️ Project Architecture

```
User Upload Resume
        │
        ▼
FastAPI Upload API
        │
        ▼
Resume Service
        │
        ▼
RAG Ingestion Pipeline
        │
        ▼
ChromaDB
```

Current Question Answering Flow (LangGraph)

```
User Question
      │
      ▼
LangGraph StateGraph
  ├─ retrieve_context   → Embedding + Semantic Search
  ├─ compose_prompt     → Prompt Construction
  └─ generate           → Llama 3.2
      │
      ▼
Answer
```

Interviewer Flow (LangGraph)

```
Start Session
      │
      ▼
Generate Opening Question (from resume context)
      │
      ▼
Candidate Submits Answer
      │
      ▼
Evaluate Answer (LLM rubric, 0-10) + Follow-up Question
      │
      ▼
Update Session Score (average) → Next Turn
```

---

## 🛠️ Tech Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL

### AI / GenAI

- Sentence Transformers
- ChromaDB
- Ollama
- Llama 3.2

### Future

- LangChain
- LangGraph
- Streamlit
- Docker
- MLflow

---

## 📂 Project Structure

```text
backend/
│
├── app/
│   ├── api/            # FastAPI routers (interviews, resume, auth, mcp, agents)
│   ├── services/       # Business logic (interview, resume, auth)
│   ├── rag/            # Ingestion + LangGraph RAG + interview_graph + prompt_builder
│   ├── mcp/            # MCP tools + server (model-context-protocol)
│   ├── agents/         # Interview agent (LangGraph)
│   ├── schemas/        # Pydantic models
│   ├── models/         # SQLAlchemy ORM (User, InterviewSession)
│   ├── core/           # Settings + database + security (JWT)
│   └── data/           # Sample resume
│
├── tests/              # Pytest suite (conftest.py adds app/ to sys.path)
├── uploads/            # Uploaded resumes (gitignored)
├── chroma_db/          # Persistent ChromaDB store (gitignored)
└── .env.example        # Copy to .env — loaded via python-dotenv

frontend/
├── app.py              # Streamlit dashboard
└── requirements.txt

Dockerfile               # Backend (FastAPI)
frontend/Dockerfile      # Streamlit
docker-compose.yml
```

Run tests from the repo root:

```bash
pytest backend/tests -q
```

Run locally:

```bash
# backend
uvicorn app.main:app --app-dir backend --port 8000
# frontend
BACKEND_URL=http://127.0.0.1:8000 streamlit run frontend/app.py --server.port 8501
```

Docker:

```bash
docker compose up --build
# api: http://localhost:8000  streamlit: http://localhost:8501  docs: http://localhost:8000/docs
```

---

## 📌 Features Implemented

- Upload Resume PDF + ingested chunks
- RAG Q&A (`POST /interview/ask`) and Interviewer Flow (`POST /interview/start`, `POST /interview/answer`)
- Generate Opening Interview Question From Resume (LLM + heuristic fallback)
- Evaluate Candidate Answers (LLM rubric 0–10 + strengths/weaknesses/feedback; offline fallback)
- Adaptive Follow-up Questions (LLM + template fallback; deduped via history)
- Session Score = rounded average (0–10) + full history (`GET /interview/session/{id}`)
- Auth (register/login/me, JWT, pbkdf2, optional ownership enforcement)
- MCP Tools (`resume_search`, `interview_start`, `interview_answer`, `interview_get`, `follow_up_hint`) via `GET /mcp/tools` + `POST /mcp/call` and stdio `python -m app.mcp.server`
- Interview Agent (LangGraph, `POST /agent/interview/*`) orchestrating via MCP tools
- Streamlit UI (upload, auth, interview loop, history, score, MCP explorer)
- Docker + Compose (api + streamlit; optional Ollama)

---

## 📖 Learning Goal

This project is being built from scratch to understand every component of a production-grade AI Engineering system instead of relying on high-level frameworks from the beginning.

The project will later be migrated to LangChain and LangGraph to understand what those frameworks abstract internally.