# Backend Dockerfile — FastAPI + LangGraph
FROM python:3.11-slim

WORKDIR /app

# system deps for building native wheels (e.g. chromadb, sentence-transformers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY pytest.ini ./

# ensure uploads/chroma dirs exist and are writable
RUN mkdir -p backend/uploads backend/chroma_db

ENV PYTHONPATH=/app/backend
ENV DATABASE_URL=sqlite:///./dev.db
ENV CHROMA_DB_PATH=/app/backend/chroma_db

EXPOSE 8000

# init db then serve
CMD ["sh", "-c", "python backend/app/init_db.py && uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend"]
