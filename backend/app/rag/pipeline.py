# from app.rag.chunker import chunk_text
from typer import prompt

from app.rag.embedding import get_embedding
from app.rag.vector_store import search_chunks
from app.rag.prompt_builder import build_prompt
from app.rag.llm import generate_answer

def run_rag_pipeline(question: str):
  
    question_embedding = get_embedding(question)

    search_results = search_chunks(question_embedding)
    

    documents = search_results["documents"][0]

    prompt = build_prompt(
        question=question,
        retrieved_chunks=documents
    )

    answer = generate_answer(prompt)

    return answer