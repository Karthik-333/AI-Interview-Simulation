import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.interview import InterviewSession
from app.services import interview_service


def _test_db(monkeypatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(interview_service, "SessionLocal", TestSessionLocal)
    return TestSessionLocal


def test_start_interview_returns_first_question(monkeypatch):
    _test_db(monkeypatch)
    monkeypatch.setattr(
        interview_service,
        "run_question_generation",
        lambda user_name, session_id=None, **kwargs: "Tell me about your FastAPI experience.",
    )

    result = interview_service.start_interview("Karthik")
    assert result["session_id"] == 1
    assert result["first_question"] == "Tell me about your FastAPI experience."


def test_submit_answer_evaluates_persists_and_scores_average(monkeypatch):
    TestSessionLocal = _test_db(monkeypatch)
    monkeypatch.setattr(
        interview_service,
        "run_question_generation",
        lambda user_name, session_id=None, **kwargs: "First question?",
    )
    monkeypatch.setattr(
        interview_service,
        "run_evaluation",
        lambda question, answer, plan=None, **kwargs: {
            "score": 8,
            "strengths": ["Clear explanation"],
            "weaknesses": [],
            "feedback": "Good depth.",
        },
    )

    start = interview_service.start_interview("Karthik")
    result = interview_service.submit_answer(start["session_id"], "I built a FastAPI backend with RAG.")

    assert result["score"] == 8
    assert result["evaluation"] == "Good depth."
    assert result["next_question"]  # should exist after generation
    assert result["current_score"] == 8

    db = TestSessionLocal()
    session = db.query(InterviewSession).first()
    assert session.current_question == result["next_question"]
    assert session.score == 8
    history = json.loads(session.history)
    assert history[0]["question"] == "First question?"
    assert history[0]["score"] == 8
    db.close()


def test_submit_answer_averages_multiple_scores(monkeypatch):
    TestSessionLocal = _test_db(monkeypatch)
    monkeypatch.setattr(
        interview_service,
        "run_question_generation",
        lambda user_name, session_id=None, **kwargs: "Q1?",
    )
    monkeypatch.setattr(
        interview_service,
        "run_evaluation",
        lambda question, answer, plan=None, **kwargs: {
            "score": 10,
            "strengths": [],
            "weaknesses": [],
            "feedback": "Strong.",
        },
    )

    start = interview_service.start_interview("Karthik")
    interview_service.submit_answer(start["session_id"], "answer one")
    result = interview_service.submit_answer(start["session_id"], "answer two")

    assert result["current_score"] == 10

    db = TestSessionLocal()
    session = db.query(InterviewSession).first()
    assert len(json.loads(session.history)) == 2
    db.close()


def test_submit_answer_uses_heuristic_fallback_when_llm_absent(monkeypatch):
    TestSessionLocal = _test_db(monkeypatch)
    monkeypatch.setattr(interview_service, "run_question_generation", lambda user_name, session_id=None, **kwargs: None)
    monkeypatch.setattr(interview_service, "run_evaluation", lambda question, answer, plan=None, **kwargs: None)

    start = interview_service.start_interview("Karthik")
    # fallback question when LLM unavailable (offline mode)
    assert start["first_question"] is not None
    assert "walk me through" in start["first_question"].lower() or "experience" in start["first_question"].lower()

    result = interview_service.submit_answer(start["session_id"], "Python is a general purpose programming language used across many domains.")
    assert result["score"] == 7
    assert result["evaluation"] == "The answer was concise."

    db = TestSessionLocal()
    session = db.query(InterviewSession).first()
    assert session.score == 7
    db.close()
