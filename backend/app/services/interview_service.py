from app.core.database import SessionLocal
from app.models.interview import InterviewSession
from app.rag.pipeline import run_rag_pipeline
def start_interview(user_name: str):
    db = SessionLocal()
    interview = InterviewSession(
        user_name=user_name,
        score=0
    )
    
    db.add(interview)
    db.commit()
    db.close()
    return {
        "message": f"Interview started for {user_name}"
    }
def ask_question(question: str):
    return run_rag_pipeline(question)