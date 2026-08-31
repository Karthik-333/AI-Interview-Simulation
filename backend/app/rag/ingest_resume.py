from app.rag.pdf_loader import extract_text_from_pdf
from app.rag.chunker import chunk_text
from app.rag.embedding import get_document_embeddings
from app.rag.vector_store import store_chunks


def ingest_resume(file_path: str):
    text = extract_text_from_pdf(file_path)
    chunks = chunk_text(text)
    embeddings = get_document_embeddings(chunks)
    store_chunks(chunks, embeddings)
    print("Resume successfully ingested.")
