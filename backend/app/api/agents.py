from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.interview_agent import agent_start_interview, agent_submit_answer

router = APIRouter(prefix="/agent", tags=["Agent"])


class AgentStartRequest(BaseModel):
    user_name: str


class AgentAnswerRequest(BaseModel):
    session_id: int
    answer: str
    user_name: str | None = None


@router.post("/interview/start")
def agent_interview_start(req: AgentStartRequest):
    out = agent_start_interview(req.user_name)
    # out is full agent state; surface useful fields
    return {
        "session_id": out.get("session_id"),
        "first_question": out.get("current_question"),
        "last_result": out.get("last_result"),
        "history": out.get("history", []),
    }


@router.post("/interview/answer")
def agent_interview_answer(req: AgentAnswerRequest):
    result = agent_submit_answer(req.session_id, req.answer, user_name=req.user_name or "Candidate")
    return result
