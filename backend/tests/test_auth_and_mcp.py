import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import create_access_token, hash_password, verify_password
from app.models.base import Base
from app.models.user import User
from app.mcp.server import call_tool, list_tools
from app.agents.interview_agent import run_interview_agent
from app.services import interview_service


def _test_db(monkeypatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(interview_service, "SessionLocal", TestSessionLocal)
    # also patch service used by mcp tools (they import from interview_service at call time)
    import app.mcp.tools as mcp_tools
    # mcp tools use interview_service.SessionLocal via import-time function closure; patch the same object
    # interview_service is already patched, so no extra action needed
    return TestSessionLocal


def test_password_hash_and_verify():
    h = hash_password("secret123")
    assert verify_password("secret123", h)
    assert not verify_password("wrong", h)


def test_jwt_create_and_decode():
    token = create_access_token({"sub": "alice"})
    from app.core.security import decode_access_token

    payload = decode_access_token(token)
    assert payload["sub"] == "alice"


def test_mcp_list_and_call(monkeypatch):
    _test_db(monkeypatch)
    tools = list_tools()
    assert any(t["name"] == "interview_start" for t in tools)
    assert any(t["name"] == "resume_search" for t in tools)
    # call interview_start via MCP
    res = call_tool("interview_start", {"user_name": "MCPUser"})
    assert res["session_id"] == 1
    assert "first_question" in res
    # call interview_get
    res2 = call_tool("interview_get", {"session_id": 1})
    assert res2["user_name"] == "MCPUser"


def test_agent_start_and_answer(monkeypatch):
    _test_db(monkeypatch)
    out = run_interview_agent("AgentUser")
    assert out["session_id"] == 1
    assert out["current_question"] is not None
    sid = out["session_id"]
    out2 = run_interview_agent("AgentUser", candidate_answer="I built a FastAPI service", session_id=sid)
    assert out2["last_result"]["score"] in range(0, 11)
    assert "next_question" in out2["last_result"]
