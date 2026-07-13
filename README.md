# AI Interview Simulation

An AI-powered interview simulation platform that generates personalized interview questions and answers based on the candidate's resume using Retrieval-Augmented Generation (RAG) and Large Language Models (LLMs).

---

## 🚀 Current Status

**Project Stage:** Phase 4 - Production AI Backend (In Progress)

### ✅ Completed

- FastAPI Backend
- PostgreSQL Integration
- SQLAlchemy ORM
- Resume PDF Processing
- Text Chunking
- SentenceTransformer Embeddings (all-MiniLM-L6-v2)
- ChromaDB Vector Store
- Semantic Search
- Ollama Integration (Llama 3.2)
- Resume Upload API
- RAG Ingestion Pipeline

## 📈 Development Progress

- ✅ Phase 1 — Backend Foundations
- ✅ Phase 2 — Database & Architecture
- ✅ Phase 3 — Build RAG From Scratch
- 🚧 Phase 4 — Production AI Backend
- ⏳ Phase 5 — LangChain
- ⏳ Phase 6 — LlamaIndex
- ⏳ Phase 7 — AI Agents & MCP
- ⏳ Phase 8 — Deployment

### 🚧 In Progress

- Interview Question API
- Prompt Pipeline
- Streamlit Frontend

### 📅 Planned

- LangChain Integration
- LlamaIndex Integration
- MLflow
- Docker
- Deployment
- Authentication

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

Current Question Answering Flow

```
User Question
      │
      ▼
Embedding
      │
      ▼
Semantic Search
      │
      ▼
Prompt Construction
      │
      ▼
Llama 3.2
      │
      ▼
Answer
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
- LlamaIndex
- Streamlit
- Docker
- MLflow

---

## 📂 Project Structure

```text
backend/
│
├── app/
│   ├── api/
│   ├── services/
│   ├── rag/
│   ├── schemas/
│   ├── models/
│   └── core/
│
├── uploads/
├── chroma_db/
└── requirements.txt
```

---

## 📌 Features Implemented

- Upload Resume PDF
- Extract Resume Text
- Generate Embeddings
- Store Embeddings in ChromaDB
- Retrieve Relevant Resume Chunks
- Generate Context-Aware Prompts
- Answer Questions Using Local LLM

---

## 📖 Learning Goal

This project is being built from scratch to understand every component of a production-grade AI Engineering system instead of relying on high-level frameworks from the beginning.

The project will later be migrated to LangChain and LlamaIndex to understand what those frameworks abstract internally.