import json
import re
from collections import Counter
from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.models.interview import InterviewSession
from app.rag.pipeline import run_rag_pipeline

try:
    from app.rag.interview_graph import run_evaluation, run_question_generation
except ImportError:  # pragma: no cover - fallback when LangGraph is unavailable

    def run_question_generation(user_name=None):  # type: ignore[no-redef]
        return None

    def run_evaluation(question, answer):  # type: ignore[no-redef]
        return None

INSUFFICIENT_CONTEXT_PHRASE = "don't have enough information"
UNCERTAINTY_PHRASES = (
    "i think",
    "maybe",
    "i am not sure",
    "not sure",
    "it seems",
)
STOPWORDS = {
    "a", "an", "and", "are", "as", "be", "because", "can", "do", "does", "for", "from",
    "how", "i", "in", "is", "it", "of", "on", "or", "that", "the", "this", "to",
    "what", "when", "where", "which", "why", "with", "you", "your",
}


def _parse_history(raw_history: str | None) -> list[dict]:
    try:
        return json.loads(raw_history or "[]")
    except Exception:
        return []


def _extract_topic(text: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9_\-]+", text or "")
    words = [token for token in tokens if token.lower() not in STOPWORDS]
    if not words:
        return "this topic"
    if len(words) == 1:
        return words[0]
    return " ".join(words[:3])


def evaluate_answer(answer: str) -> tuple[int, str]:
    normalized = (answer or "").strip().lower()
    if not normalized or INSUFFICIENT_CONTEXT_PHRASE in normalized:
        return 0, "insufficient_context"

    if any(phrase in normalized for phrase in UNCERTAINTY_PHRASES):
        return 1, "uncertain"

    if len(normalized.split()) >= 40:
        return 2, "detailed"

    return 1, "concise"


def generate_follow_up_question(question: str, answer: str, history: list[dict] | None = None) -> str:
    history = history or []
    topic = _extract_topic(question)
    answer_topic = _extract_topic(answer)
    recent_questions = Counter(_extract_topic(entry.get("question", "")) for entry in history[-3:])
    repeated_topic = recent_questions.most_common(1)[0][0] if recent_questions else None

    if INSUFFICIENT_CONTEXT_PHRASE in (answer or "").lower():
        return f"Could you narrow down what you mean by {topic}?"

    if any(phrase in (answer or "").lower() for phrase in UNCERTAINTY_PHRASES):
        return f"Can you walk me through a concrete example of {topic}?"

    if len((answer or "").split()) >= 40:
        if repeated_topic and repeated_topic != "this topic":
            return f"What trade-offs would you consider next for {repeated_topic}?"
        return f"What trade-offs or edge cases would you consider next for {answer_topic}?"

    # concise: prefer answer topic if meaningful, else question topic
    chosen = answer_topic if answer_topic != "this topic" else topic
    return f"Can you elaborate on the implementation details of {chosen}?"


def start_interview(user_name: str, user_id: int | None = None):
    db = SessionLocal()
    interview = InterviewSession(
        user_name=user_name,
        user_id=user_id,
        score=0,
        history="[]",
    )

    db.add(interview)
    db.commit()
    db.refresh(interview)
    session_id = interview.id

    first_question = run_question_generation(user_name)
    if not first_question:
        first_question = _fallback_first_question(user_name)
    interview.current_question = first_question
    db.commit()
    db.close()

    return {
        "session_id": session_id,
        "message": f"Interview started for {user_name}",
        "first_question": first_question,
    }


def ask_question(question: str, session_id: int | None = None):
    answer = run_rag_pipeline(question)
    score_delta, evaluation = evaluate_answer(answer)
    next_question = generate_follow_up_question(question, answer)

    if session_id is not None:
        db = SessionLocal()
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if session:
            history = _parse_history(session.history)
            # legacy score_delta plus normalized 0-10 score for unified history
            normalized = {0: 0, 1: 5, 2: 9}.get(score_delta, 0)
            history.append(
                {
                    "question": question,
                    "answer": answer,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "score": normalized,
                    "score_delta": score_delta,
                    "evaluation": evaluation,
                    "next_question": next_question,
                }
            )
            session.history = json.dumps(history)
            # keep legacy additive for backward compat, but also ensure score reflects average if needed
            session.score = (session.score or 0) + score_delta
            db.commit()
            current_score = session.score or 0
        else:
            current_score = None
        db.close()
    else:
        current_score = None

    return {
        "answer": answer,
        "evaluation": evaluation,
        "score_delta": score_delta,
        "next_question": next_question,
        "session_id": session_id,
        "current_score": current_score,
    }


def _heuristic_evaluation(answer: str) -> dict:
    """Fallback evaluation used when the LLM is unavailable. Maps the existing
    keyword heuristics onto a 0-10 score."""
    normalized = (answer or "").strip().lower()
    if not normalized or INSUFFICIENT_CONTEXT_PHRASE in normalized:
        score = 0
        feedback = "The answer did not provide enough information."
    elif any(phrase in normalized for phrase in UNCERTAINTY_PHRASES):
        score = 5
        feedback = "The answer was vague or uncertain."
    elif len(normalized.split()) >= 40:
        score = 9
        feedback = "The answer was detailed."
    else:
        score = 7
        feedback = "The answer was concise."
    return {
        "score": score,
        "strengths": [] if score == 0 else [feedback],
        "weaknesses": [] if score >= 5 else [feedback],
        "feedback": feedback,
    }


def _fallback_first_question(user_name: str | None = None) -> str:
    """Offline fallback when LLM is unavailable. Uses a resume-aware template
    if chunks exist, otherwise a generic opening question."""
    try:
        from app.rag.vector_store import get_all_chunks  # local import to avoid cycle

        chunks = get_all_chunks(limit=1)
        if chunks:
            topic = _extract_topic(chunks[0])
            if topic != "this topic":
                return f"Tell me about your experience with {topic} — what's a concrete outcome you delivered?"
    except Exception:
        pass
    name_part = f", {user_name}" if user_name else ""
    return f"Thanks{name_part} — could you walk me through the most impactful project on your resume and your specific role in it?"


def _normalize_score(entry: dict) -> int:
    """Return a 0-10 score for any history entry, handling both new (score) and
    legacy (score_delta) formats."""
    if "score" in entry and isinstance(entry["score"], int):
        return entry["score"]
    if entry.get("score") is not None:
        try:
            return int(entry["score"])
        except Exception:
            pass
    delta = entry.get("score_delta")
    if isinstance(delta, int):
        return {0: 0, 1: 5, 2: 9}.get(delta, 0)
    return 0


def _next_question_fallback(question: str, answer: str) -> str:
    return generate_follow_up_question(question, answer)


def submit_answer(session_id: int, answer: str):
    db = SessionLocal()
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        db.close()
        return None

    question = session.current_question
    if not question:
        question = _extract_topic(answer)

    evaluation = run_evaluation(question, answer)
    if evaluation is None:
        evaluation = _heuristic_evaluation(answer)
        next_question = _next_question_fallback(question, answer)
    else:
        next_question = evaluation.get("next_question") or _next_question_fallback(question, answer)

    score = evaluation["score"]

    history = _parse_history(session.history)
    history.append(
        {
            "question": question,
            "answer": answer,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "score": score,
            "score_delta": None,
            "evaluation": evaluation["feedback"],
            "next_question": next_question,
        }
    )
    session.history = json.dumps(history)

    scores = [_normalize_score(e) for e in history]
    current_score = round(sum(scores) / len(scores)) if scores else 0
    session.score = current_score
    session.current_question = next_question
    db.commit()
    db.close()

    return {
        "score": score,
        "evaluation": evaluation["feedback"],
        "strengths": evaluation.get("strengths", []),
        "weaknesses": evaluation.get("weaknesses", []),
        "next_question": next_question,
        "current_score": current_score,
    }


def get_interview_session(session_id: int):
    db = SessionLocal()
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        db.close()
        return None

    history = _parse_history(session.history)
    # normalize legacy entries so API always returns both fields
    for entry in history:
        if "score" not in entry or entry["score"] is None:
            if isinstance(entry.get("score_delta"), int):
                entry["score"] = {0: 0, 1: 5, 2: 9}.get(entry["score_delta"], 0)
            else:
                entry["score"] = entry.get("score")
        if "score_delta" not in entry:
            entry["score_delta"] = None
        if "next_question" not in entry:
            entry["next_question"] = None

    payload = {
        "session_id": session.id,
        "user_name": session.user_name,
        "score": session.score or 0,
        "history": history,
        "suggested_next_question": (
            generate_follow_up_question(history[-1]["question"], history[-1]["answer"], history[:-1])
            if history
            else f"What would you like to explore next with {session.user_name}?"
        ),
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }
    db.close()
    return payload
