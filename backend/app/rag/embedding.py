# from sentence_transformers import SentenceTransformer
# from app.core.settings import EMBEDDING_MODEL
# model = SentenceTransformer(EMBEDDING_MODEL)

# def get_embedding(text: str):
#     return model.encode(text)
from langchain_huggingface import HuggingFaceEmbeddings
    
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

def get_document_embeddings(chunks: list[str]) -> list[list[float]]:
    """
    Generate embeddings for document chunks.
    """
    return embeddings.embed_documents(chunks)


def get_query_embedding(question: str) -> list[float]:
    """
    Generate embedding for a search query.
    """
    return embeddings.embed_query(question)