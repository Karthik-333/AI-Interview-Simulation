# from app.rag.chunker import chunk_text
from app.rag.embedding import get_embedding
from app.rag.vector_store import search_chunks
from app.rag.prompt_builder import build_prompt
from app.rag.llm import generate_answer

def run_rag_pipeline(question: str):
  
    question_embedding = get_embedding(question)

    results = search_chunks(question_embedding)
    
    results = results['documents'][0]

    prompt = build_prompt(question=question, results=results)

    answer = generate_answer(prompt)

    return answer