import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

load_dotenv(BACKEND_DIR / ".env")

UPLOAD_DIR = BACKEND_DIR / "uploads"
CHROMA_DB_PATH = Path(os.getenv("CHROMA_DB_PATH", str(BACKEND_DIR / "chroma_db")))

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-please-set-env")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REQUIRE_AUTH = os.getenv("REQUIRE_AUTH", "false").lower() in ("1", "true", "yes")
