from app.core.database import SessionLocal
from app.models.interview import InterviewSession

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