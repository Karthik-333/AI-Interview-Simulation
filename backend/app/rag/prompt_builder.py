def build_prompt(question: str, retrieved_chunks: list[str]):

    context = "\n\n".join(retrieved_chunks)

    prompt = f"""You are an AI interview assistant.
    
Answer ONLY using the context below.

If the answer is not present in the context,
say "I don't have enough information."

Context:
{context}

Question:
{question}

Answer:
"""

    return prompt