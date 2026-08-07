import json
from datetime import datetime
from app.core.database import SessionLocal
from app.models.interview import InterviewSession
from app.rag.pipeline import run_rag_pipeline


def start_interview(user_name: str):
    db = SessionLocal()
    interview = InterviewSession(
        user_name=user_name,
        score=0,
        history="[]"
    )

    db.add(interview)
    db.commit()
    db.refresh(interview)
    session_id = interview.id
    db.close()
    return {
        "session_id": session_id,
        "message": f"Interview started for {user_name}"
    }


def ask_question(question: str, session_id: int | None = None):
    answer = run_rag_pipeline(question)

    if session_id is not None:
        db = SessionLocal()
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if session:
            try:
                history = json.loads(session.history or "[]")
            except Exception:
                history = []

            history.append({
                "question": question,
                "answer": answer,
                "timestamp": datetime.utcnow().isoformat()
            })

            session.history = json.dumps(history)
            db.commit()
        db.close()

    return answer
