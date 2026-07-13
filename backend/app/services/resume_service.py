from pathlib import Path
import shutil
from app.core.settings import UPLOAD_DIR
from app.rag.ingest_resume import ingest_resume
from fastapi import UploadFile, HTTPException


def save_uploaded_file(file: UploadFile):
    # Define the directory where you want to save the uploaded file
    # upload_dir = Path(__file__).resolve().parent.parent.parent / "uploads"
    
    # upload_dir.mkdir(parents=True, exist_ok=True)

    # Define the path for the uploaded file
    file_path = UPLOAD_DIR / file.filename

    # Save the uploaded file to the specified path
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return str(file_path)  # Return the path of the saved file as a string

def upload_resume(file: UploadFile):
    
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF file.")
    
    file_path = save_uploaded_file(file)

    ingest_resume(file_path)
    
    return {"message": "Resume uploaded and ingested successfully."}


    