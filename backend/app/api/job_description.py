from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.job_description_service import attach_job_description

router = APIRouter(prefix="/job-description", tags=["Job Description"])


class JobDescriptionRequest(BaseModel):
    session_id: int
    job_description: str = Field(min_length=1, max_length=20_000)


@router.post("/attach")
def attach_job_description_endpoint(request: JobDescriptionRequest):
    """Persist a plain-text job description on an interview session."""
    try:
        result = attach_job_description(request.session_id, request.job_description)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not result.get("stored"):
        raise HTTPException(status_code=404, detail="Interview session not found.")
    return {
        "session_id": result["session_id"],
        "job_description": result["job_description"],
        "stored": result["stored"],
    }
