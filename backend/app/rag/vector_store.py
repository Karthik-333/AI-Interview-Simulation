import chromadb
from app.core.settings import CHROMA_DB_PATH

client = chromadb.PersistentClient(path=str(CHROMA_DB_PATH))

collection = client.get_or_create_collection(
    name="resume_chunks"
)

def store_chunks(chunks, embeddings):

    for i, chunk in enumerate(chunks):

        collection.add(
            ids=[str(i)],
            documents=[chunk],
            embeddings=[embeddings[i]],
            metadatas=[
                {
                    "source": "resume"
                }
            ]
        )

def search_chunks(query_embedding):

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=2
    )

    return results      
  
def show_all_chunks():
    return collection.get()