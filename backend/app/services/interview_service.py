import json
import re
from collections import Counter
from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.models.interview import AuditLog, InterviewSession
from app.rag.pipeline import run_rag_pipeline
from app.services.scoring_service import analyze_response, score_answer
from app.api.webhooks import notify

try:
    from app.rag.interview_graph import run_evaluation, run_question_generation, run_next_question_generation
except ImportError:  # pragma: no cover - fallback when LangGraph is unavailable

    def run_question_generation(user_name=None, **kwargs):  # type: ignore[no-redef]
        return None

    def run_evaluation(question, answer, **kwargs):  # type: ignore[no-redef]
        return None

    def run_next_question_generation(question, candidate_answer, **kwargs):  # type: ignore[no-redef]
        return ""

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


def _parse_session_plan(raw_plan: str | None) -> list[dict]:
    if not raw_plan:
        return []
    try:
        data = json.loads(raw_plan)
    except Exception:
        return []
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        sections = data.get("sections") if isinstance(data.get("sections"), list) else []
        return [item for item in sections if isinstance(item, dict)]
    return []


def _plan_section_for_session(session: InterviewSession | None):
    if not session:
        return None, 0
    plan = _parse_session_plan(session.plan)
    if not plan:
        return None, 0
    index = max(0, min(int(session.current_section_index or 0), len(plan) - 1))
    return plan[index], index


def _answer_matches_expectation(answer: str, expectation: str) -> bool:
    if not expectation:
        return False
    candidate = (answer or "").lower()
    target = expectation.lower()
    tokens = set(re.findall(r"[a-z0-9]+", target))
    if not tokens:
        return False
    return any(token in candidate for token in tokens)


def evaluate_answer(answer: str) -> tuple[int, str]:
    normalized = (answer or "").strip().lower()
    if not normalized or INSUFFICIENT_CONTEXT_PHRASE in normalized:
        return 0, "insufficient_context"

    if any(phrase in normalized for phrase in UNCERTAINTY_PHRASES):
        return 1, "uncertain"

    if len(normalized.split()) >= 40:
        return 2, "detailed"

    return 1, "concise"


def generate_follow_up_question(
    question: str,
    answer: str,
    history: list[dict] | None = None,
    session_id: int | None = None,
    plan: list[dict] | None = None,
) -> str:
    history = history or []
    topic = _extract_topic(question)
    answer_topic = _extract_topic(answer)
    recent_questions = Counter(_extract_topic(entry.get("question", "")) for entry in history[-3:])
    repeated_topic = recent_questions.most_common(1)[0][0] if recent_questions else None

    if plan:
        section = plan[0]
        expectations = section.get("expectations") or []
        if expectations:
            for expectation in expectations:
                if _answer_matches_expectation(answer, expectation):
                    continue
                label = section.get("label") or section.get("topic") or "this section"
                return f"For {label}, can you elaborate on: {expectation}?"
            label = section.get("label") or section.get("topic") or "this section"
            if len(plan) > 1:
                next_section = plan[1]
                next_label = next_section.get("label") or next_section.get("topic") or "next area"
                return f"Let's shift to {next_label}: how have you handled {next_section.get('topic', 'this area')} in practice?"
            return f"For {label}, what trade-off or edge case would you call out?"

    response_kind = analyze_response(answer)
    if INSUFFICIENT_CONTEXT_PHRASE in (answer or "").lower():
        return f"Could you narrow down what you mean by {topic}?"

    if any(phrase in (answer or "").lower() for phrase in UNCERTAINTY_PHRASES):
        return f"Can you walk me through a concrete example of {topic}?"

    if response_kind == "detailed":
        if repeated_topic and repeated_topic != "this topic":
            return f"What trade-offs would you consider next for {repeated_topic}?"
        return f"What trade-offs or edge cases would you consider next for {answer_topic}?"

    chosen = answer_topic if answer_topic != "this topic" else topic
    return f"Can you elaborate on the implementation details of {chosen}?"


def start_interview(user_name: str, user_id: int | None = None):
    db = SessionLocal()
    try:
        interview = InterviewSession(user_name=user_name, user_id=user_id, score=0, history="[]")
        db.add(interview)
        db.commit()
        db.refresh(interview)
        session_id = interview.id

        first_question = run_question_generation(user_name, session_id=interview.id) or _fallback_first_question(user_name)
        interview.current_question = first_question
        db.add(AuditLog(event_type="interview_started", session_id=interview.id, actor_id=user_id, payload=json.dumps({"user_name": user_name})))
        db.commit()
    except Exception:
        db.rollback()
        db.close()
        raise
    db.close()
    notify("interview_started", {"session_id": session_id, "user_name": user_name})

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
            db.add(AuditLog(event_type="answer_recorded", session_id=session.id, payload=json.dumps({"evaluation": evaluation, "score_delta": score_delta})))
            # keep legacy additive for backward compat, but also ensure score reflects average if needed
            session.score = (session.score or 0) + score_delta
            db.commit()
            current_score = session.score or 0
        else:
            current_score = None
        db.close()
    else:
        current_score = None

    rubric = score_answer(answer, question)
    return {
        "answer": answer,
        "evaluation": evaluation,
        "score_delta": score_delta,
        "next_question": next_question,
        "session_id": session_id,
        "current_score": current_score,
        "dimensions": rubric["dimensions"],
        "factuality": rubric["factuality"],
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
    rubric = score_answer(answer)
    return {
        "score": score,
        "strengths": [] if score == 0 else [feedback],
        "weaknesses": [] if score >= 5 else [feedback],
        "feedback": feedback,
        "dimensions": rubric["dimensions"],
        "factuality": rubric["factuality"],
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


def _next_question_fallback(question: str, answer: str, session: InterviewSession | None = None) -> str:
    plan = _parse_session_plan(session.plan) if session and session.plan else None
    return generate_follow_up_question(question, answer, session_id=session.id if session else None, plan=plan)


def create_session_plan(session_id: int) -> dict | None:
    db = SessionLocal()
    try:
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if not session or not session.job_description:
            return None
        from app.rag.plan_graph import run_plan_generation

        plan = run_plan_generation(session.job_description)
        if not plan:
            return None
        session.plan = json.dumps(plan)
        session.current_section_index = 0
        db.commit()
        db.refresh(session)
        return {"session_id": session.id, "plan": plan, "current_section_index": session.current_section_index}
    finally:
        db.close()


def submit_answer(session_id: int, answer: str, audio_path: str | None = None):
    db = SessionLocal()
    try:
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if not session:
            return None

        question = session.current_question or _extract_topic(answer)
        plan = _parse_session_plan(session.plan) if session.plan else None

        evaluation = run_evaluation(question, answer, plan=plan)
        if evaluation is None:
            evaluation = _heuristic_evaluation(answer)
            next_question = _next_question_fallback(question, answer, session)
        else:
            next_question = run_next_question_generation(question, answer, evaluation=evaluation, plan=plan) or _next_question_fallback(
                question, answer, session
            )

        score = evaluation["score"]

        history = _parse_history(session.history)
        prior_context = [entry.get("answer", "") for entry in history[-4:]]
        evaluation.setdefault("dimensions", score_answer(answer, question, prior_context)["dimensions"])
        history_entry = {
            "question": question,
            "answer": answer,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "score": score,
            "score_delta": None,
            "evaluation": evaluation["feedback"],
            "next_question": next_question,
            "dimensions": evaluation["dimensions"],
        }
        if audio_path:
            history_entry["audio_path"] = audio_path
        history.append(history_entry)
        session.history = json.dumps(history)

        scores = [_normalize_score(e) for e in history]
        current_score = round(sum(scores) / len(scores)) if scores else 0
        session.score = current_score
        session.current_question = next_question
        db.add(
            AuditLog(
                event_type="answer_submitted",
                session_id=session.id,
                payload=json.dumps({"score": score, "response_kind": analyze_response(answer)}),
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    notify("answer_submitted", {"session_id": session_id, "score": score})

    return {
        "score": score,
        "evaluation": evaluation["feedback"],
        "strengths": evaluation.get("strengths", []),
        "weaknesses": evaluation.get("weaknesses", []),
        "next_question": next_question,
        "current_score": current_score,
    }


def finalize_interview(session_id: int) -> dict | None:
    """Finalize a session and generate a comprehensive report.
    If a plan exists, uses it for assessment; otherwise uses the questions actually asked.
    """
    from app.rag.report_graph import run_report_generation

    db = SessionLocal()
    try:
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if not session:
            return None

        history = _parse_history(session.history)
        plan = _parse_session_plan(session.plan) if session.plan else None

        if plan:
            report = run_report_generation(plan, history)
            if report:
                session.report = json.dumps(report)
                db.commit()
                db.refresh(session)
                return {
                    "session_id": session.id,
                    "report": report,
                    "finalized": True,
                }
        return {
            "session_id": session.id,
            "report": None,
            "finalized": False,
            "reason": "No plan available for report generation.",
        }
    finally:
        db.close()


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
        if "audio_path" not in entry:
            entry["audio_path"] = None

    plan = _parse_session_plan(session.plan)
    payload = {
        "session_id": session.id,
        "user_name": session.user_name,
        "score": session.score or 0,
        "job_description": session.job_description,
        "plan": plan,
        "current_section_index": session.current_section_index or 0,
        "report": json.loads(session.report) if session.report else None,
        "history": history,
        "suggested_next_question": (
            generate_follow_up_question(history[-1]["question"], history[-1]["answer"], history[:-1], session_id=session.id, plan=plan)
            if history
            else f"What would you like to explore next with {session.user_name}?"
        ),
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }
    db.close()
    return payload
