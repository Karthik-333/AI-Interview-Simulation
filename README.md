# AI Interview Simulation

An AI-powered interview simulation platform that generates personalized interview questions, evaluates candidate responses, and supports authenticated interview sessions using a FastAPI backend and a modern React frontend.

---

## 🚀 Current Status

**Project Stage:** Production-ready frontend + backend interview platform

### ✅ Completed

- FastAPI backend with CORS and modular route/service architecture
- SQLAlchemy ORM with SQLite default and PostgreSQL-ready configuration
- Resume upload + PDF ingestion pipeline for semantic interview grounding
- RAG-based question answering and interview session orchestration
- LangGraph/LangChain-backed interview flow with fallback heuristics
- Auth and security layer with register/login/me endpoints and JWT support
- Modern React + TypeScript + Vite frontend with Tailwind CSS
- shadcn/ui-inspired component system for production-style UI
- React Query for API data fetching, React Hook Form for forms, Zustand for frontend state
- Deployment-ready Docker configuration and environment setup

---

## 🏗️ Architecture

```text
User
 │
 ▼
React + Vite Frontend
 │
 ▼
FastAPI Backend
 │
 ├─ Resume API
 ├─ Auth API
 ├─ Interview API
 ├─ RAG / vector retrieval
 └─ LangGraph orchestration
 │
 ▼
Resume + vector store + interview evaluation pipeline
```

### Interview flow

```text
Start session
  │
  ▼
Generate opening question from resume context
  │
  ▼
Candidate submits answer
  │
  ▼
Evaluate answer (score + strengths + weaknesses)
  │
  ▼
Generate next question / follow-up
  │
  ▼
Persist session history and score
```

---

## 🛠️ Tech Stack

### Frontend

- React 18
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui-inspired components
- React Query
- React Hook Form
- Zustand

### Backend

- Python
- FastAPI
- SQLAlchemy
- JWT auth
- ChromaDB
- Sentence Transformers
- LangChain / LangGraph
- Ollama integration with offline fallback

---

## 📂 Project Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── rag/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── agents/
│   │   ├── mcp/
│   │   ├── data/
│   │   ├── main.py
│   │   └── init_db.py
│   ├── tests/
│   ├── uploads/
│   └── chroma_db/
├── frontend/
│   ├── src/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
├── README.md
└── .gitignore
```

---

## 🔧 Local Development

### Backend

```bash
cd /home/karthik/Projects/AI-Interview-Simulation-v2
pip install -r requirements.txt
python backend/app/init_db.py
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd /home/karthik/Projects/AI-Interview-Simulation-v2/frontend
npm install
cp .env.example .env
npm run dev
```

Frontend runs on:

- http://localhost:5173

Backend runs on:

- http://localhost:8000

API docs:

- http://localhost:8000/docs

---

## 🧪 Testing

```bash
cd /home/karthik/Projects/AI-Interview-Simulation-v2
pytest backend/tests -q
```

---

## 📌 Features Implemented

- Upload and ingest resume PDFs
- Personalized interview question generation from resume context
- Candidate answer evaluation with score, strengths, and weaknesses
- Adaptive follow-up question generation
- Persistent interview session tracking and score history
- Authentication support for interview workflows
- Production-oriented frontend dashboard experience
- Backend API integration with FastAPI and modern React UI

---

## 🚢 Docker / Deployment

```bash
docker compose up --build
```

This brings up the API and frontend services together for local deployment testing.

---

## 📖 Notes

The system is designed as a practical AI engineering project combining retrieval, interview logic, model orchestration, and production-facing UX. The frontend has been modernized to a React-based stack to better align with production application expectations while preserving the backend interview capabilities.
