"""Deterministic, explainable interview scoring used with or without an LLM."""

import re
from collections import Counter

RUBRIC_DIMENSIONS = ("technical_depth", "communication", "problem_solving", "domain_expertise")
_STOPWORDS = {"a", "an", "and", "are", "as", "be", "by", "for", "from", "in", "is", "it", "of", "on", "or", "the", "to", "with"}


def _tokens(text: str) -> list[str]:
    return [word for word in re.findall(r"[a-z0-9]+", (text or "").lower()) if word not in _STOPWORDS]


def semantic_match(answer: str, ideal_answer: str) -> float:
    """Return a bounded token-level semantic overlap score."""
    left, right = set(_tokens(answer)), set(_tokens(ideal_answer))
    if not left or not right:
        return 0.0
    return round(len(left & right) / len(left | right), 3)


def validate_factuality(answer: str, context: list[str]) -> dict:
    """Flag unsupported claims using conservative context token coverage."""
    answer_tokens = set(_tokens(answer))
    context_tokens = set(_tokens(" ".join(context)))
    unsupported = sorted(token for token in answer_tokens - context_tokens if len(token) > 5)
    ratio = len(answer_tokens & context_tokens) / max(len(answer_tokens), 1)
    return {"is_supported": ratio >= 0.25 or not answer_tokens, "support_ratio": round(ratio, 3), "unsupported_terms": unsupported[:10]}


def score_answer(answer: str, question: str = "", context: list[str] | None = None, ideal_answer: str = "") -> dict:
    """Score four dimensions from observable answer signals and return feedback."""
    words = _tokens(answer)
    context = context or []
    factuality = validate_factuality(answer, context)
    length_score = min(len(words) / 35, 1.0)
    technical = min(1.0, length_score * 0.55 + (0.45 if any(t in words for t in ("api", "database", "algorithm", "system", "code", "test")) else 0))
    communication = min(1.0, 0.45 + (0.35 if len(words) >= 12 else 0) + (0.2 if "." in answer else 0))
    problem_solving = min(1.0, length_score * 0.7 + (0.3 if any(t in words for t in ("because", "tradeoff", "approach", "solved", "debug")) else 0))
    domain = max(0.0, min(1.0, factuality["support_ratio"] if context else length_score))
    dimensions = {name: round(value * 10, 2) for name, value in zip(RUBRIC_DIMENSIONS, (technical, communication, problem_solving, domain))}
    match = semantic_match(answer, ideal_answer) if ideal_answer else 0.0
    score = round(sum(dimensions.values()) / len(dimensions))
    if not answer.strip():
        score = 0
    return {"score": max(0, min(10, score)), "dimensions": dimensions, "semantic_match": match, "factuality": factuality}


def analyze_response(answer: str) -> str:
    """Classify a response for adaptive follow-up generation."""
    words = _tokens(answer)
    if not words:
        return "missing"
    if len(words) < 10:
        return "concise"
    if any(term in words for term in ("uncertain", "maybe", "guess", "unsure")):
        return "uncertain"
    if len(words) >= 35:
        return "detailed"
    return "developing"
