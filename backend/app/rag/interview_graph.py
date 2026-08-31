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


def _retrieve_chunks(query: str, n_results: int = DEFAULT_RETRIEVAL) -> list[str]:
    embedding = get_query_embedding(query)
    results = search_chunks(embedding, n_results=n_results)
    documents = results.get("documents") or [[]]
    return documents[0] if documents else []


def _sample_resume_chunks(limit: int = DEFAULT_RESUME_SAMPLE) -> list[str]:
    return get_all_chunks(limit=limit)


# --- Question generation graph ---


def sample_context(state: InterviewState) -> InterviewState:
    return {**state, "resume_chunks": _sample_resume_chunks()}


def compose_question_prompt(state: InterviewState) -> InterviewState:
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


def run_question_generation(user_name: str | None = None) -> str | None:
    """Generate an opening interview question from the resume. None if LLM unavailable."""
    if not LLM_AVAILABLE:
        return None
    result = question_graph.invoke({"user_name": user_name})
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


def compose_follow_up(state: InterviewState) -> InterviewState:
    if not state.get("evaluation"):
        return {**state, "next_question": ""}
    prompt = build_follow_up_prompt(
        question=state["question"],
        candidate_answer=state.get("candidate_answer", ""),
        evaluation=state["evaluation"],
        resume_chunks=state.get("resume_chunks", []),
    )
    return {**state, "next_question": generate_answer(prompt).strip()}


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


def run_evaluation(question: str, candidate_answer: str) -> dict | None:
    """Evaluate a candidate answer. Returns dict with score/strengths/weaknesses/
    feedback/next_question, or None if the LLM is unavailable."""
    if not LLM_AVAILABLE:
        return None
    result = evaluation_graph.invoke(
        {"question": question, "candidate_answer": candidate_answer}
    )
    evaluation = result.get("evaluation")
    if not evaluation:
        return None
    return {
        "score": int(evaluation.get("score", 0)),
        "strengths": evaluation.get("strengths", []),
        "weaknesses": evaluation.get("weaknesses", []),
        "feedback": evaluation.get("feedback", ""),
        "next_question": result.get("next_question", ""),
    }