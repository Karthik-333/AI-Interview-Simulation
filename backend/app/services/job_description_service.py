from __future__ import annotations

from app.core.database import SessionLocal
from app.models.interview import InterviewSession
from app.rag.plan_graph import run_plan_generation

MAX_JOB_DESCRIPTION_LENGTH = 20_000
MIN_JOB_DESCRIPTION_LENGTH = 1


def validate_job_description(job_description: str) -> str:
    """Validate and normalize a job description before persisting it."""
    if job_description is None:
        raise ValueError("Job description is required.")

    normalized = job_description.strip()
    if len(normalized) < MIN_JOB_DESCRIPTION_LENGTH:
        raise ValueError("Job description must not be empty.")
    if len(normalized) > MAX_JOB_DESCRIPTION_LENGTH:
        raise ValueError(
            f"Job description exceeds the maximum allowed length of {MAX_JOB_DESCRIPTION_LENGTH} characters."
        )
    return normalized


def attach_job_description(session_id: int, job_description: str) -> dict[str, object]:
    """Attach a raw job description to a session row in the interview session model."""
    cleaned = validate_job_description(job_description)
    db = SessionLocal()
    try:
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if session is None:
            return {"session_id": session_id, "job_description": None, "stored": False}

        session.job_description = cleaned
        db.commit()
        db.refresh(session)

        plan = run_plan_generation(cleaned)
        if plan:
            session.plan = __import__("json").dumps(plan)
            session.current_section_index = 0
            db.commit()
            db.refresh(session)

        return {
            "session_id": session.id,
            "job_description": session.job_description,
            "stored": True,
        }
    finally:
        db.close()
