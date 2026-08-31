import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.interview import InterviewSession
from app.services import interview_service


def test_start_and_ask_update_history_score_and_follow_up(monkeypatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    monkeypatch.setattr(interview_service, "SessionLocal", TestSessionLocal)
    monkeypatch.setattr(interview_service, "run_rag_pipeline", lambda question: "Python is a programming language used for web development and automation.")

    result = interview_service.start_interview("Karthik")
    assert result["session_id"] == 1

    response = interview_service.ask_question("What is Python?", session_id=result["session_id"])
    assert response["answer"].startswith("Python is a programming language")
    assert response["evaluation"] == "concise"
    assert response["score_delta"] == 1
    assert response["next_question"].startswith("Can you elaborate")
    assert response["current_score"] == 1

    db = TestSessionLocal()
    session = db.query(InterviewSession).first()
    assert session.user_name == "Karthik"
    assert session.score == 1
    assert json.loads(session.history)[0]["question"] == "What is Python?"
    assert json.loads(session.history)[0]["next_question"].startswith("Can you elaborate")
    db.close()
