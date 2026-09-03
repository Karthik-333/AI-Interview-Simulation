from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.rag.embedding import get_query_embedding
from app.rag.llm import LLM_AVAILABLE, generate_answer, generate_structured_json
from app.rag.prompt_builder import (
    build_evaluation_prompt,
    build_follow_up_prompt,
    build_question_prompt,
)
from app.rag.vector_store import get_all_chunks, search_chunks

DEFAULT_RESUME_SAMPLE = 4
DEFAULT_RETRIEVAL = 2


class InterviewState(TypedDict, total=False):
    user_name: str
    resume_chunks: list[str]
    question: str
    candidate_answer: str
    evaluation: dict
    next_question: str
    prompt: str
    evaluation_prompt: str
    plan: list[dict]
    current_section_index: int
    next_question_prompt: str


def _retrieve_chunks(query: str, n_results: int = DEFAULT_RETRIEVAL) -> list[str]:
    embedding = get_query_embedding(query)
    results = search_chunks(embedding, n_results=n_results, query=query)
    documents = results.get("documents") or [[]]
    return documents[0] if documents else []


def _sample_resume_chunks(limit: int = DEFAULT_RESUME_SAMPLE) -> list[str]:
    return get_all_chunks(limit=limit)


def _derives_plan_for_session(session_id: int | None = None, user_name: str | None = None) -> list[dict]:
    if session_id is None:
        return []
    try:
        from app.core.database import SessionLocal
        from app.models.interview import InterviewSession

        db = SessionLocal()
        try:
            session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
            if not session or not session.plan:
                return []
            import json

            try:
                plan = json.loads(session.plan)
            except Exception:
                return []
            return plan if isinstance(plan, list) else []
        finally:
            db.close()
    except Exception:
        return []


def _plan_section_from_state(state: InterviewState) -> tuple[dict | None, int]:
    plan = state.get("plan") or []
    if not plan:
        return None, 0
    index = max(0, min(int(state.get("current_section_index") or 0), len(plan) - 1))
    return plan[index], index


# --- Question generation graph ---


def sample_context(state: InterviewState) -> InterviewState:
    return {**state, "resume_chunks": _sample_resume_chunks()}


def compose_question_prompt(state: InterviewState) -> InterviewState:
    section, _ = _plan_section_from_state(state)
    if section:
        expectations = section.get("expectations") or []
        expectation_text = " ".join(expectations[:3])
        topic = section.get("label") or section.get("topic") or "this area"
        prompt = (
            f"You are interviewing a candidate for a role. Ground the question in the section '{topic}' and its explicit expectations: {expectation_text}. "
            f"Use the candidate resume context below when relevant, but do not ignore job-relevant expectations.\n\n"
            f"Resume context:\n{chr(10).join(state.get('resume_chunks', []))}\n\n"
            f"Ask ONE focused interview question that probes this section and starts naturally. Do not include preamble or explanation."
        )
    else:
        prompt = build_question_prompt(
            resume_chunks=state.get("resume_chunks", []),
            user_name=state.get("user_name"),
        )
    return {**state, "prompt": prompt}


def generate_question(state: InterviewState) -> InterviewState:
    answer = generate_answer(state["prompt"])
    return {**state, "question": answer.strip()}


def build_question_graph():
    graph = StateGraph(InterviewState)
    graph.add_node("sample_context", sample_context)
    graph.add_node("compose_question_prompt", compose_question_prompt)
    graph.add_node("generate_question", generate_question)
    graph.set_entry_point("sample_context")
    graph.add_edge("sample_context", "compose_question_prompt")
    graph.add_edge("compose_question_prompt", "generate_question")
    graph.add_edge("generate_question", END)
    return graph.compile()


question_graph = build_question_graph()


def run_question_generation(user_name: str | None = None, session_id: int | None = None) -> str | None:
    """Generate an opening interview question from the resume or a loaded plan. None if LLM unavailable."""
    if not LLM_AVAILABLE:
        return None
    plan = _derives_plan_for_session(session_id)
    result = question_graph.invoke({"user_name": user_name, "plan": plan, "current_section_index": 0})
    return result.get("question")


# --- Evaluation graph ---
def retrieve_for_question(state: InterviewState) -> InterviewState:
    return {
        **state,
        "resume_chunks": _retrieve_chunks(state.get("question", ""))
        or _sample_resume_chunks(),
    }


def compose_evaluation_prompt(state: InterviewState) -> InterviewState:
    prompt = build_evaluation_prompt(
        question=state["question"],
        candidate_answer=state.get("candidate_answer", ""),
        resume_chunks=state.get("resume_chunks", []),
    )
    return {**state, "evaluation_prompt": prompt}


def evaluate_answer(state: InterviewState) -> InterviewState:
    data = generate_structured_json(state["evaluation_prompt"])
    return {**state, "evaluation": data or {}}


def generate_follow_up_question(state: InterviewState) -> InterviewState:
    section, idx = _plan_section_from_state(state)
    if section and state.get("candidate_answer"):
        expectations = section.get("expectations") or []
        for expectation in expectations:
            if expectation.lower() in (state.get("candidate_answer") or "").lower():
                continue
            prompt = (
                f"You are continuing a structured interview. Current section: {section.get('label') or section.get('topic')}. "
                f"Expectations: {'; '.join(expectations)}. The candidate answer is: {state.get('candidate_answer', '')}. "
                f"Ask ONE concise follow-up question that probes the next unmet expectation and stays grounded in the current section."
            )
            return {**state, "next_question": generate_answer(prompt).strip()}
    if not state.get("evaluation"):
        return {**state, "next_question": ""}
    prompt = build_follow_up_prompt(
        question=state["question"],
        candidate_answer=state.get("candidate_answer", ""),
        evaluation=state["evaluation"],
        resume_chunks=state.get("resume_chunks", []),
    )
    return {**state, "next_question": generate_answer(prompt).strip()}


def compose_follow_up(state: InterviewState) -> InterviewState:
    return generate_follow_up_question(state)


def build_evaluation_graph():
    graph = StateGraph(InterviewState)
    graph.add_node("retrieve_for_question", retrieve_for_question)
    graph.add_node("compose_evaluation_prompt", compose_evaluation_prompt)
    graph.add_node("evaluate_answer", evaluate_answer)
    graph.add_node("compose_follow_up", compose_follow_up)
    graph.set_entry_point("retrieve_for_question")
    graph.add_edge("retrieve_for_question", "compose_evaluation_prompt")
    graph.add_edge("compose_evaluation_prompt", "evaluate_answer")
    graph.add_edge("evaluate_answer", "compose_follow_up")
    graph.add_edge("compose_follow_up", END)
    return graph.compile()


evaluation_graph = build_evaluation_graph()


def run_next_question_generation(
    question: str,
    candidate_answer: str,
    evaluation: dict | None = None,
    resume_chunks: list[str] | None = None,
    plan: list[dict] | None = None,
) -> str:
    """Generate only the next question without requiring a full rubric evaluation pass."""
    if not LLM_AVAILABLE:
        return ""
    if plan:
        section = plan[0] if isinstance(plan, list) and plan else None
        if section:
            expectations = section.get("expectations") or []
            for expectation in expectations:
                if expectation.lower() not in (candidate_answer or "").lower():
                    return f"For {section.get('label') or section.get('topic') or 'this section'}, can you elaborate on: {expectation}?"
    prompt = build_follow_up_prompt(
        question=question,
        candidate_answer=candidate_answer,
        evaluation=evaluation or {"feedback": ""},
        resume_chunks=resume_chunks or _sample_resume_chunks(),
    )
    return generate_answer(prompt).strip()


def run_evaluation(question: str, candidate_answer: str, plan: list[dict] | None = None) -> dict | None:
    """Evaluate a candidate answer. Returns dict with score/strengths/weaknesses/
    feedback, or None if the LLM is unavailable. Does NOT include next_question."""
    if not LLM_AVAILABLE:
        return None
    result = evaluation_graph.invoke(
        {"question": question, "candidate_answer": candidate_answer, "plan": plan or []}
    )
    evaluation = result.get("evaluation")
    if not evaluation:
        return None
    dimensions = evaluation.get("dimensions") or {}
    score = max(0, min(10, int(evaluation.get("score", 0))))
    return {
        "score": score,
        "strengths": evaluation.get("strengths", []),
        "weaknesses": evaluation.get("weaknesses", []),
        "feedback": evaluation.get("feedback", ""),
        "dimensions": dimensions,
        "factuality": evaluation.get("factuality", {}),
    }