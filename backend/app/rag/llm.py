import json
import re

from app.core.settings import LLM_MODEL

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
    if chat_model is not None:
        response = chat_model.invoke(prompt)
        return response.content

    if ollama is not None:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return response["message"]["content"]

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
