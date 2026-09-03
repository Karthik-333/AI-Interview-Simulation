from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.services import interview_service
from app.services import job_description_service
from app.services.job_description_service import attach_job_description


def _test_db(monkeypatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(interview_service, "SessionLocal", TestSessionLocal)
    monkeypatch.setattr(job_description_service, "SessionLocal", TestSessionLocal)
    return TestSessionLocal


def test_job_description_is_accepted_and_persisted_on_the_session(monkeypatch):
    _test_db(monkeypatch)
    monkeypatch.setattr(
        interview_service,
        "run_question_generation",
        lambda user_name, session_id=None, **kwargs: "Tell me about your most impactful project.",
    )

    created = interview_service.start_interview("Karthik")
    jd = "We are seeking a backend engineer with Python, FastAPI, SQLAlchemy, and distributed system experience."

    stored = attach_job_description(created["session_id"], jd)
    assert stored["stored"] is True
    assert stored["job_description"] == jd

    session = interview_service.get_interview_session(created["session_id"])
    assert session is not None
    assert session["job_description"] == jd

    try:
        attach_job_description(created["session_id"], "")
        assert False, "empty job description should be rejected"
    except ValueError:
        pass

    try:
        attach_job_description(created["session_id"], "x" * 20_001)
        assert False, "oversized job description should be rejected"
    except ValueError:
        pass


def test_omitting_job_description_keeps_resume_only_interview_unchanged(monkeypatch):
    _test_db(monkeypatch)
    monkeypatch.setattr(interview_service, "run_question_generation", lambda user_name, session_id=None, **kwargs: "First question?")

    created = interview_service.start_interview("Karthik")
    session = interview_service.get_interview_session(created["session_id"])

    assert session is not None
    assert session["job_description"] is None
    assert session["history"] == []
    assert session["suggested_next_question"] == "What would you like to explore next with Karthik?"
