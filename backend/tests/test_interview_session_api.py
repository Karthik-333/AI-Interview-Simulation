import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.interview import InterviewSession
from app.services import interview_service


def test_get_session_and_no_score_increment_on_insufficient_context(monkeypatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    monkeypatch.setattr(interview_service, "SessionLocal", TestSessionLocal)
    monkeypatch.setattr(interview_service, "run_rag_pipeline", lambda question: "I don't have enough information.")

    result = interview_service.start_interview("Karthik")
    response = interview_service.ask_question("What is LangGraph?", session_id=result["session_id"])
    assert response["answer"] == "I don't have enough information."
    assert response["evaluation"] == "insufficient_context"
    assert response["score_delta"] == 0
    assert response["next_question"].startswith("Could you narrow down")

    session = interview_service.get_interview_session(result["session_id"])
    assert session["score"] == 0
    assert session["history"][0]["evaluation"] == "insufficient_context"
    assert session["history"][0]["score_delta"] == 0
    assert session["history"][0]["question"] == "What is LangGraph?"
    assert session["suggested_next_question"].startswith("Could you narrow down")

    db = TestSessionLocal()
    persisted = db.query(InterviewSession).first()
    assert json.loads(persisted.history)[0]["evaluation"] == "insufficient_context"
    db.close()
