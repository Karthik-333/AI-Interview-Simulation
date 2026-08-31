import json
import re
import logging
import time

from app.core.settings import LLM_MAX_RETRIES, LLM_MODEL, LLM_RETRY_BASE_SECONDS

logger = logging.getLogger(__name__)

try:
    from langchain_ollama import ChatOllama
except ImportError:  # pragma: no cover - fallback for lean environments
    ChatOllama = None

if ChatOllama is None:
    try:
        import ollama
    except ImportError:  # pragma: no cover - final fallback
        ollama = None

chat_model = ChatOllama(model=LLM_MODEL) if ChatOllama is not None else None

LLM_AVAILABLE = chat_model is not None or ollama is not None


def generate_answer(prompt: str):
    """Generate text with bounded exponential backoff for transient failures."""
    last_error = None
    for attempt in range(LLM_MAX_RETRIES + 1):
        try:
            if chat_model is not None:
                response = chat_model.invoke(prompt)
                return response.content
            if ollama is not None:
                response = ollama.chat(model=LLM_MODEL, messages=[{"role": "user", "content": prompt}])
                return response["message"]["content"]
            break
        except Exception as exc:
            last_error = exc
            if attempt >= LLM_MAX_RETRIES:
                logger.warning("llm_call_failed", exc_info=True)
                break
            time.sleep(LLM_RETRY_BASE_SECONDS * (2**attempt))
    if last_error is not None:
        return ""

    return prompt


def _extract_json(text: str) -> dict | None:
    if not text:
        return None
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def generate_structured_json(prompt: str) -> dict | None:
    """Return parsed JSON from the LLM, or None if it is unavailable/not parseable."""
    if not LLM_AVAILABLE:
        return None
    return _extract_json(generate_answer(prompt))
