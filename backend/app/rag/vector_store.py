import chromadb

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(
    name="resume_chunks"
)


def store_chunks(chunks, embeddings):

    for i, chunk in enumerate(chunks):

        collection.add(
            ids=[str(i)],

            documents=[chunk],

            embeddings=[embeddings[i].tolist()],

            metadatas=[
                {
                    "source": "resume"
                }
            ]
        )
def search_chunks(query_embedding):

    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=2
    )

    return results      
  
def show_all_chunks():
    return collection.get()