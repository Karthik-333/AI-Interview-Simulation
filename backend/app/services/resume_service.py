from pathlib import Path
from uuid import uuid4
import shutil

from fastapi import HTTPException, UploadFile

from app.core.settings import UPLOAD_DIR
from app.rag.ingest_resume import ingest_resume


def save_uploaded_file(file: UploadFile):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    original_name = Path(file.filename).name
    suffix = Path(original_name).suffix
    safe_name = f"{Path(original_name).stem}-{uuid4().hex[:12]}{suffix}"
    file_path = UPLOAD_DIR / safe_name

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return str(file_path)


def upload_resume(file: UploadFile):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF file.")

    file_path = save_uploaded_file(file)

    try:
        ingest_resume(file_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Resume ingestion failed.") from exc

    return {"message": "Resume uploaded and ingested successfully.", "file_path": file_path}
