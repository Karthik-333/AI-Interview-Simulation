"""MCP tools for AI Interview Simulation.

Each tool is a plain function with a JSON-serializable return.
MCP server (app.mcp.server) and REST fallback (app.api.mcp) both import from here.
"""
from typing import Any

from app.services.interview_service import (
    create_session_plan,
    finalize_interview,
    get_interview_session,
    start_interview,
    submit_answer,
)
from app.rag.vector_store import search_chunks
from app.rag.embedding import get_query_embedding


def tool_resume_search(query: str, n_results: int = 3) -> dict[str, Any]:
    """Semantic search over ingested resume chunks."""
    embedding = get_query_embedding(query)
    results = search_chunks(embedding, n_results=n_results)
    docs = (results.get("documents") or [[]])[0]
    metas = (results.get("metadatas") or [[]])[0] if results.get("metadatas") else []
    return {"query": query, "documents": docs, "metadatas": metas, "count": len(docs)}


def tool_interview_start(user_name: str) -> dict[str, Any]:
    """Start a new interview session; returns session_id and first_question."""
    return start_interview(user_name)


def tool_interview_answer(session_id: int, answer: str) -> dict[str, Any] | None:
    """Submit a candidate answer; returns evaluation (score 0-10, strengths, etc.) + next_question."""
    return submit_answer(session_id, answer)


def tool_interview_get(session_id: int) -> dict[str, Any] | None:
    """Fetch full interview session including history and current score."""
    return get_interview_session(session_id)


def tool_interview_create_plan(session_id: int) -> dict[str, Any] | None:
    """Generate and persist an interview plan from a session's job description.
    Only succeeds if job_description exists on the session."""
    return create_session_plan(session_id) or {"session_id": session_id, "error": "No job description on session"}


def tool_interview_generate_report(session_id: int) -> dict[str, Any] | None:
    """Finalize an interview session and generate a report from the transcript against the plan.
    Returns the report if a plan exists; otherwise returns an error message."""
    return finalize_interview(session_id) or {"session_id": session_id, "error": "Session not found"}


def tool_generate_follow_up_hint(session_id: int) -> dict[str, Any] | None:
    """Convenience: return the suggested next question for a session."""
    sess = get_interview_session(session_id)
    if not sess:
        return None
    return {"session_id": session_id, "suggested_next_question": sess.get("suggested_next_question")}


# registry used by MCP server and REST API
TOOL_REGISTRY: dict[str, dict[str, Any]] = {
    "resume_search": {
        "fn": tool_resume_search,
        "description": "Semantic search over resume chunks. Args: query, n_results",
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}, "n_results": {"type": "integer", "default": 3}}, "required": ["query"]},
    },
    "interview_start": {
        "fn": tool_interview_start,
        "description": "Start interview session. Args: user_name",
        "input_schema": {"type": "object", "properties": {"user_name": {"type": "string"}}, "required": ["user_name"]},
    },
    "interview_answer": {
        "fn": tool_interview_answer,
        "description": "Submit answer for evaluation. Args: session_id, answer",
        "input_schema": {"type": "object", "properties": {"session_id": {"type": "integer"}, "answer": {"type": "string"}}, "required": ["session_id", "answer"]},
    },
    "interview_get": {
        "fn": tool_interview_get,
        "description": "Get interview session. Args: session_id",
        "input_schema": {"type": "object", "properties": {"session_id": {"type": "integer"}}, "required": ["session_id"]},
    },
    "interview_create_plan": {
        "fn": tool_interview_create_plan,
        "description": "Create interview plan from job description. Args: session_id",
        "input_schema": {"type": "object", "properties": {"session_id": {"type": "integer"}}, "required": ["session_id"]},
    },
    "interview_generate_report": {
        "fn": tool_interview_generate_report,
        "description": "Finalize interview and generate report. Args: session_id",
        "input_schema": {"type": "object", "properties": {"session_id": {"type": "integer"}}, "required": ["session_id"]},
    },
    "follow_up_hint": {
        "fn": tool_generate_follow_up_hint,
        "description": "Get suggested next question. Args: session_id",
        "input_schema": {"type": "object", "properties": {"session_id": {"type": "integer"}}, "required": ["session_id"]},
    },
}
