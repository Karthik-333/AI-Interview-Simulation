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

# Production controls.  Every value is environment-configurable so local
# development retains the existing lightweight defaults.
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))
LLM_RETRY_BASE_SECONDS = float(os.getenv("LLM_RETRY_BASE_SECONDS", "0.25"))
RAG_CACHE_TTL_SECONDS = int(os.getenv("RAG_CACHE_TTL_SECONDS", "300"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
API_VERSION = os.getenv("API_VERSION", "v1")
STT_PROVIDER = os.getenv("STT_PROVIDER", "groq").lower()
STT_API_KEY = os.getenv("STT_API_KEY")
STT_MODEL = os.getenv("STT_MODEL", "whisper-large-v3-turbo")
STT_TIMEOUT_SECONDS = float(os.getenv("STT_TIMEOUT_SECONDS", "30"))
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "gemini").lower()
TTS_API_KEY = os.getenv("TTS_API_KEY")
TTS_MODEL = os.getenv("TTS_MODEL", "gemini-2.5-flash-preview-tts")
TTS_VOICE = os.getenv("TTS_VOICE", "Kore")
TTS_TIMEOUT_SECONDS = float(os.getenv("TTS_TIMEOUT_SECONDS", "15"))
AUDIO_STORAGE_PATH = Path(os.getenv("AUDIO_STORAGE_PATH", str(BACKEND_DIR / "audio")))
ENABLE_AUDIO_PERSISTENCE = os.getenv("ENABLE_AUDIO_PERSISTENCE", "false").lower() in ("1", "true", "yes")
