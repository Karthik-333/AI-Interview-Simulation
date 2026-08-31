from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class InterviewRequest(BaseModel):
    user_name: str = Field(min_length=1, max_length=120)


class InterviewStartResponse(BaseModel):
    session_id: int
    message: str
    first_question: Optional[str] = None


class AnswerSubmissionRequest(BaseModel):
    session_id: int
    answer: str = Field(min_length=1, max_length=20_000)


class AnswerEvaluationResponse(BaseModel):
    score: int
    evaluation: str
    strengths: list[str]
    weaknesses: list[str]
    next_question: str
    current_score: int
    dimensions: dict[str, float] = Field(default_factory=dict)
    factuality: dict = Field(default_factory=dict)


class InterviewQuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2_000)
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
    dimensions: Optional[dict[str, float]] = None
    audio_path: Optional[str] = None


class InterviewSessionResponse(BaseModel):
    session_id: int
    user_name: str
    score: int
    history: list[InterviewHistoryEntry]
    suggested_next_question: Optional[str] = None
    created_at: datetime
    updated_at: datetime
