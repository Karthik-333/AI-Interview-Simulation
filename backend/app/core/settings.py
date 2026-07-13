from pathlib import Path

# AI-Interview-Simulation/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# AI-Interview-Simulation/backend/
BACKEND_DIR = PROJECT_ROOT / "backend"

# AI-Interview-Simulation/backend/uploads/
UPLOAD_DIR = BACKEND_DIR / "uploads"

# AI-Interview-Simulation/backend/chroma_db/
CHROMA_DB_PATH = BACKEND_DIR / "chroma_db"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
LLM_PROVIDER = "ollama"
LLM_MODEL = "llama3.2"