from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.rag.embedding import get_query_embedding
from app.rag.llm import generate_answer
from app.rag.prompt_builder import build_prompt
from app.rag.vector_store import search_chunks


class RagState(TypedDict, total=False):
    question: str
    question_embedding: list[float]
    search_results: dict
    retrieved_chunks: list[str]
    prompt: str
    answer: str


def retrieve_context(state: RagState) -> RagState:
    question_embedding = get_query_embedding(state["question"])
    search_results = search_chunks(question_embedding)
    documents = search_results.get("documents") or [[]]
    retrieved_chunks = documents[0] if documents else []
    return {
        **state,
        "question_embedding": question_embedding,
        "search_results": search_results,
        "retrieved_chunks": retrieved_chunks,
    }


def compose_prompt(state: RagState) -> RagState:
    prompt = build_prompt(
        question=state["question"],
        retrieved_chunks=state.get("retrieved_chunks", []),
    )
    return {**state, "prompt": prompt}


def generate(state: RagState) -> RagState:
    answer = generate_answer(state["prompt"])
    return {**state, "answer": answer}


def build_rag_graph():
    graph = StateGraph(RagState)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("compose_prompt", compose_prompt)
    graph.add_node("generate", generate)
    graph.set_entry_point("retrieve_context")
    graph.add_edge("retrieve_context", "compose_prompt")
    graph.add_edge("compose_prompt", "generate")
    graph.add_edge("generate", END)
    return graph.compile()


rag_graph = build_rag_graph()


def run_langgraph_rag_pipeline(question: str) -> str:
    result = rag_graph.invoke({"question": question})
    return result["answer"]
