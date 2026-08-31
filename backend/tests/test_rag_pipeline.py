def _patch_langgraph_pipeline(monkeypatch):
    import app.rag.langgraph_pipeline as langgraph_pipeline

    monkeypatch.setattr(langgraph_pipeline, "get_query_embedding", lambda question: [0.1, 0.2])
    monkeypatch.setattr(
        langgraph_pipeline,
        "search_chunks",
        lambda embedding: {"documents": [["resume chunk"]]},
    )
    monkeypatch.setattr(
        langgraph_pipeline,
        "build_prompt",
        lambda question, retrieved_chunks: f"{question}::{retrieved_chunks[0]}",
    )
    monkeypatch.setattr(
        langgraph_pipeline,
        "generate_answer",
        lambda prompt: f"answer::{prompt}",
    )


def _patch_fallback_pipeline(monkeypatch):
    from app.rag import pipeline

    monkeypatch.setattr(pipeline, "get_embedding", lambda text: [0.1, 0.2])
    monkeypatch.setattr(
        pipeline,
        "search_chunks",
        lambda embedding: {"documents": [["resume chunk"]]},
    )
    monkeypatch.setattr(
        pipeline,
        "build_prompt",
        lambda question, retrieved_chunks: f"{question}::{retrieved_chunks[0]}",
    )
    monkeypatch.setattr(
        pipeline,
        "generate_answer",
        lambda prompt: f"answer::{prompt}",
    )


def test_run_rag_pipeline_end_to_end(monkeypatch):
    try:
        import app.rag.langgraph_pipeline  # noqa: F401
    except ImportError:
        _patch_fallback_pipeline(monkeypatch)
    else:
        _patch_langgraph_pipeline(monkeypatch)

    from app.rag.pipeline import run_rag_pipeline

    assert (
        run_rag_pipeline("Tell me about yourself")
        == "answer::Tell me about yourself::resume chunk"
    )
