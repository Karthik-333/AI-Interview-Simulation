from sentence_transformers import SentenceTransformer
from app.core.settings import EMBEDDING_MODEL
model = SentenceTransformer(EMBEDDING_MODEL)

def get_embedding(text: str):
    return model.encode(text)