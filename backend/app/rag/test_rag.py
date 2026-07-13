# backend/app/rag/test_rag.py
# from app.rag.pipeline import run_rag_pipeline

# resume = """Karthik knows Python and FastAPI.
# Built Legal Advisory System using NLP.
# Built Insurance Anomaly Detection System."""

# query = input("Enter your question: ")
# answer = run_rag_pipeline(query)
# print("Answer:", answer)

from app.rag.vector_store import show_all_chunks

print(show_all_chunks())