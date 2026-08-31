try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:  # pragma: no cover - fallback for lean environments
    HuggingFaceEmbeddings = None

from app.core.settings import EMBEDDING_MODEL


class _FallbackEmbeddings:
    def embed_documents(self, chunks: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in chunks]

    def embed_query(self, question: str) -> list[float]:
        return self._embed(question)

    @staticmethod
    def _embed(text: str) -> list[float]:
        vector = [0.0] * 8
        for index, byte in enumerate(text.encode("utf-8")):
            vector[index % len(vector)] += byte / 255.0
        return vector


embeddings = (
    HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    if HuggingFaceEmbeddings is not None
    else _FallbackEmbeddings()
)


def get_document_embeddings(chunks: list[str]) -> list[list[float]]:
    return embeddings.embed_documents(chunks)


def get_query_embedding(question: str) -> list[float]:
    return embeddings.embed_query(question)


def get_embedding(text: str) -> list[float]:
    return get_query_embedding(text)
