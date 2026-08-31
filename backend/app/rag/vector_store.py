"""Resume retrieval with semantic, lexical, cached, and re-ranked search."""

import math
import re
import uuid
from functools import lru_cache

try:
    import chromadb
except ImportError:  # pragma: no cover
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
            self._rows.extend({"id": i, "document": d, "embedding": e, "metadata": m} for i, d, e, m in zip(ids, documents, embeddings, metadatas))
        def query(self, query_embeddings, n_results=2):
            docs = [row["document"] for row in self._rows[:n_results]]
            return {"documents": [docs]}
        def get(self):
            return self._rows
    collection = _InMemoryCollection()


def store_chunks(chunks, embeddings):
    ids = [f"resume-{uuid.uuid4().hex[:12]}-{i}" for i in range(len(chunks))]
    collection.add(ids=ids, documents=chunks, embeddings=embeddings, metadatas=[{"source": "resume"} for _ in chunks])
    get_all_chunks.cache_clear()


def _lexical_score(query: str, document: str) -> float:
    query_terms = set(re.findall(r"[a-z0-9]+", query.lower()))
    document_terms = re.findall(r"[a-z0-9]+", document.lower())
    if not query_terms or not document_terms:
        return 0.0
    return sum(1 + math.log(document_terms.count(term)) for term in query_terms if term in document_terms) / len(query_terms)


def expand_query(query: str) -> list[str]:
    """Create low-risk lexical variants without requiring an LLM."""
    terms = re.findall(r"[a-z0-9]+", query.lower())
    return [query, " ".join(terms), " ".join(terms + ["experience"]), " ".join(terms + ["project"])]


def search_chunks(query_embedding, n_results: int = 2, query: str = ""):
    """Retrieve a wider candidate set and re-rank by lexical relevance."""
    results = collection.query(query_embeddings=[query_embedding], n_results=max(n_results * 4, n_results))
    documents = (results.get("documents") or [[]])[0]
    if query and documents:
        documents = sorted(documents, key=lambda doc: max(_lexical_score(variant, doc) for variant in expand_query(query)), reverse=True)
    return {"documents": [documents[:n_results]]}


@lru_cache(maxsize=256)
def get_all_chunks(limit: int | None = None) -> list[str]:
    rows = collection.get()
    if isinstance(rows, list):
        return [row["document"] for row in rows[:limit]]
    return rows.get("documents", [])[:limit]


def show_all_chunks():
    return collection.get()
