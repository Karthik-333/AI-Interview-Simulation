from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user_optional
from app.models.user import User
from app.schemas.interview import (
    AnswerEvaluationResponse,
    AnswerSubmissionRequest,
    InterviewQuestionRequest,
    InterviewQuestionResponse,
    InterviewRequest,
    InterviewSessionResponse,
    InterviewStartResponse,
)
from app.services.interview_service import (
    ask_question,
    get_interview_session,
    start_interview,
    submit_answer,
)

router = APIRouter()


@router.get("/")
def home():
    return {
        "message": "Welcome to AI Interview Simulation"
    }


@router.get("/health")
def health():
    return {
        "status": "Healthy"
    }


@router.post("/interview/start", response_model=InterviewStartResponse)
def interview_start(
    request: InterviewRequest, current_user: User | None = Depends(get_current_user_optional)
):
    # if authenticated, prefer authenticated username
    user_name = current_user.username if current_user else request.user_name
    user_id = current_user.id if current_user else None
    return start_interview(user_name, user_id=user_id)


@router.post("/interview/answer", response_model=AnswerEvaluationResponse)
def interview_answer(
    request: AnswerSubmissionRequest, current_user: User | None = Depends(get_current_user_optional)
):
    # ownership check when auth is enabled and session is owned
    if current_user:
        from app.core.database import SessionLocal
        from app.models.interview import InterviewSession

        db = SessionLocal()
        sess = db.query(InterviewSession).filter(InterviewSession.id == request.session_id).first()
        db.close()
        if sess and sess.user_id is not None and sess.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized for this interview session")
    result = submit_answer(request.session_id, request.answer)
    if result is None:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    return result


@router.post("/interview/ask", response_model=InterviewQuestionResponse)
def interview_ask(request: InterviewQuestionRequest):
    result = ask_question(request.question, session_id=request.session_id)
    return InterviewQuestionResponse(**result)


@router.get("/interview/session/{session_id}", response_model=InterviewSessionResponse)
def interview_session(session_id: int, current_user: User | None = Depends(get_current_user_optional)):
    # ownership check
    if current_user:
        from app.core.database import SessionLocal
        from app.models.interview import InterviewSession

        db = SessionLocal()
        sess = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        db.close()
        if sess and sess.user_id is not None and sess.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized for this interview session")
    session = get_interview_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    return session
