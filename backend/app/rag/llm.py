import ollama
from app.core.settings import LLM_MODEL

def generate_answer(prompt: str):

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]