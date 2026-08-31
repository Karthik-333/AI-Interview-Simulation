try:
    from app.rag.langgraph_pipeline import run_langgraph_rag_pipeline
except ImportError:  # pragma: no cover - fallback when LangGraph is unavailable
    from app.rag.embedding import get_embedding
    from app.rag.vector_store import search_chunks
    from app.rag.prompt_builder import build_prompt
    from app.rag.llm import generate_answer

    def run_langgraph_rag_pipeline(question: str):
        question_embedding = get_embedding(question)
        search_results = search_chunks(question_embedding)
        documents = search_results.get("documents", [[]])[0]
        prompt = build_prompt(question=question, retrieved_chunks=documents)
        return generate_answer(prompt)


def run_rag_pipeline(question: str):
    return run_langgraph_rag_pipeline(question)
