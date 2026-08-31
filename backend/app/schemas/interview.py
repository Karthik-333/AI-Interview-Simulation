from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class InterviewRequest(BaseModel):
    user_name: str


class InterviewStartResponse(BaseModel):
    session_id: int
    message: str
    first_question: Optional[str] = None


class AnswerSubmissionRequest(BaseModel):
    session_id: int
    answer: str


class AnswerEvaluationResponse(BaseModel):
    score: int
    evaluation: str
    strengths: list[str]
    weaknesses: list[str]
    next_question: str
    current_score: int


class InterviewQuestionRequest(BaseModel):
    question: str
    session_id: Optional[int] = None


class InterviewQuestionResponse(BaseModel):
    answer: str
    evaluation: str
    score_delta: int
    next_question: str
    session_id: Optional[int] = None
    current_score: Optional[int] = None


class InterviewHistoryEntry(BaseModel):
    question: str
    answer: str
    timestamp: datetime
    score: Optional[int] = None
    score_delta: Optional[int] = None
    evaluation: str
    next_question: Optional[str] = None


class InterviewSessionResponse(BaseModel):
    session_id: int
    user_name: str
    score: int
    history: list[InterviewHistoryEntry]
    suggested_next_question: Optional[str] = None
    created_at: datetime
    updated_at: datetime
