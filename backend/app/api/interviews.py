from fastapi import APIRouter
from app.schemas.interview import InterviewRequest, User
from app.services.interview_service import start_interview
from app.schemas.interview import InterviewQuestionRequest, InterviewQuestionResponse
from app.services.interview_service import ask_question

router = APIRouter()

@router.get("/")
def home():
    return {
        "message" : "Welcome to AI Interview Stimulation"
    }

@router.get("/health")
def health():
    return {
        "status" : "Healthy"
    }

@router.post("/interview/start")
def interview_start(request: InterviewRequest):
    return start_interview(request.user_name)

@router.post("/test")
def test(user: User):
    return user 

@router.get("/users/{user_id}")
def get_user(user_id: int):
    return {
        "user_id": user_id
    }
@router.post("/interview/ask")
def interview_ask(request: InterviewQuestionRequest):
    answer = ask_question(request.question)
    return InterviewQuestionResponse(answer=answer)