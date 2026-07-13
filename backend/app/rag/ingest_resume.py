# from pathlib import Path

from app.rag.pdf_loader import extract_text_from_pdf
from app.rag.chunker import chunk_text
from app.rag.embedding import get_embedding
from app.rag.vector_store import store_chunks


def ingest_resume(file_path: str):

    # BASE_DIR = Path(__file__).resolve().parent.parent

    # resume_path = BASE_DIR / "data" / "Karthik_S_Resume.pdf"

    text = extract_text_from_pdf(file_path)

    chunks = chunk_text(text)

    embeddings = [get_embedding(chunk) for chunk in chunks]

    store_chunks(chunks, embeddings)

    print("Resume successfully ingested.")


# if __name__ == "__main__":
#     ingest_resume()