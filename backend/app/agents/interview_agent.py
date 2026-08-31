"""Interview Agent — LangGraph-based agent that can call MCP tools.

The agent demonstrates Phase 7: it orchestrates resume retrieval + interview
evaluation via tool calls instead of direct function imports, so the same tools
can be exposed via MCP.

Graph: decide → (tool_call) → observe → decide → … → finish
For now a deterministic 2-step agent: start → evaluate loop, with LLM-driven
decision when available and heuristic fallback otherwise.
"""
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.mcp.tools import tool_interview_answer, tool_interview_start, tool_resume_search
from app.rag.llm import LLM_AVAILABLE, generate_answer

AGENT_SYSTEM_PROMPT = """You are an AI interview orchestrator. You have tools:
- resume_search(query): semantic search over resume
- interview_start(user_name)
- interview_answer(session_id, answer)

Decide the next tool to call based on the conversation history.
Return JSON: {"tool": "<name>", "arguments": {...}} or {"action": "finish"}
"""


class AgentState(TypedDict, total=False):
    user_name: str
    session_id: int | None
    current_question: str | None
    candidate_answer: str | None
    history: list[dict[str, Any]]
    next_action: dict[str, Any] | None
    last_result: Any
    done: bool


def _decide_next(state: AgentState) -> AgentState:
    # heuristic policy: if no session → start; if has question but no answer → wait; if has answer → evaluate
    if not state.get("session_id"):
        return {**state, "next_action": {"tool": "interview_start", "arguments": {"user_name": state.get("user_name", "Candidate")}}}

    if state.get("candidate_answer"):
        return {
            **state,
            "next_action": {
                "tool": "interview_answer",
                "arguments": {"session_id": state["session_id"], "answer": state["candidate_answer"]},
            },
        }

    # optionally use LLM to decide (when available) — otherwise fallback to resume_search for context
    if LLM_AVAILABLE:
        try:
            prompt = f"{AGENT_SYSTEM_PROMPT}\nHistory: {state.get('history', [])}\nCurrent question: {state.get('current_question')}\nSession: {state.get('session_id')}\nDecide next tool in JSON."
            raw = generate_answer(prompt).strip()
            import json, re

            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                parsed = json.loads(m.group(0))
                if "tool" in parsed:
                    return {**state, "next_action": parsed}
        except Exception:
            pass

    # default: no-op
    return {**state, "next_action": {"action": "finish"}}


def _call_tool(state: AgentState) -> AgentState:
    action = state.get("next_action") or {}
    if action.get("action") == "finish":
        return {**state, "done": True}
    tool = action.get("tool")
    args = action.get("arguments", {})
    try:
        if tool == "interview_start":
            res = tool_interview_start(**args)
            return {
                **state,
                "session_id": res.get("session_id"),
                "current_question": res.get("first_question"),
                "last_result": res,
                "history": [*state.get("history", []), {"tool": tool, "args": args, "result": res}],
            }
        if tool == "interview_answer":
            res = tool_interview_answer(**args)
            nxt = res.get("next_question") if isinstance(res, dict) else None
            return {
                **state,
                "current_question": nxt or state.get("current_question"),
                "last_result": res,
                "candidate_answer": None,  # consumed
                "history": [*state.get("history", []), {"tool": tool, "args": args, "result": res}],
            }
        if tool == "resume_search":
            res = tool_resume_search(**args)
            return {**state, "last_result": res, "history": [*state.get("history", []), {"tool": tool, "args": args, "result": res}]}
    except Exception as exc:
        return {**state, "last_result": {"error": str(exc)}, "history": [*state.get("history", []), {"tool": tool, "error": str(exc)}]}
    return {**state, "last_result": None}


def _should_continue(state: AgentState) -> str:
    if state.get("done"):
        return END
    # if we just started, continue to decide again; agent is single-turn unless candidate_answer provided
    # so finish after one tool call unless there is pending answer
    if state.get("candidate_answer"):
        return "call_tool"
    return END


def build_agent_graph():
    g = StateGraph(AgentState)
    g.add_node("decide", _decide_next)
    g.add_node("call_tool", _call_tool)
    g.set_entry_point("decide")
    g.add_edge("decide", "call_tool")
    g.add_conditional_edges("call_tool", _should_continue, {END: END, "call_tool": "decide"})
    return g.compile()


agent_graph = build_agent_graph()


def run_interview_agent(user_name: str, candidate_answer: str | None = None, session_id: int | None = None) -> dict[str, Any]:
    """Run the interview agent for one turn. Returns the final state."""
    init: AgentState = {
        "user_name": user_name,
        "session_id": session_id,
        "candidate_answer": candidate_answer,
        "history": [],
    }
    result = agent_graph.invoke(init)
    return dict(result)


# convenience for API
def agent_start_interview(user_name: str) -> dict[str, Any]:
    return run_interview_agent(user_name)


def agent_submit_answer(session_id: int, answer: str, user_name: str = "Candidate") -> dict[str, Any]:
    # we don't have user_name stored, but keep it for completeness
    out = run_interview_agent(user_name, candidate_answer=answer, session_id=session_id)
    return out.get("last_result") or {}
