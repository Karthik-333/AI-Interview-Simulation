# import os   
# print("Current Working Directory:")
# print(os.getcwd())
from app.rag.pdf_loader import extract_text_from_pdf
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

file_path = BASE_DIR / "data" / "Karthik_S_Resume.pdf"



# file_path = "app/data/Karthik_S_Resume.pdf"

text = extract_text_from_pdf(file_path)

print("\nExtracted Text:\n")
print(text)