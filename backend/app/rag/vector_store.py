import uuid

try:
    import chromadb
except ImportError:  # pragma: no cover - fallback for lean environments
    chromadb = None

from app.core.settings import CHROMA_DB_PATH

if chromadb is not None:
    client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))
    collection = client.get_or_create_collection(name="resume_chunks")
else:
    class _InMemoryCollection:
        def __init__(self):
            self._rows = []

        def add(self, ids, documents, embeddings, metadatas):
            for row in zip(ids, documents, embeddings, metadatas):
                self._rows.append({
                    "id": row[0],
                    "document": row[1],
                    "embedding": row[2],
                    "metadata": row[3],
                })

        def query(self, query_embeddings, n_results=2):
            documents = [[row["document"] for row in self._rows[:n_results]]]
            return {"documents": documents}

        def get(self):
            return self._rows

    collection = _InMemoryCollection()


def store_chunks(chunks, embeddings):
    ids = [f"resume-{uuid.uuid4().hex[:12]}-{i}" for i in range(len(chunks))]
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=[{"source": "resume"} for _ in chunks],
    )


def search_chunks(query_embedding, n_results: int = 2):
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )


def get_all_chunks(limit: int | None = None) -> list[str]:
    rows = collection.get()
    if isinstance(rows, list):
        return [row["document"] for row in rows[:limit]]
    return rows.get("documents", [])[:limit]


def show_all_chunks():
    return collection.get()
