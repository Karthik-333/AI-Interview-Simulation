from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.core.settings import UPLOAD_DIR
from app.core.settings import MAX_UPLOAD_BYTES
from app.rag.ingest_resume import ingest_resume


def save_uploaded_file(file: UploadFile):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    original_name = Path(file.filename).name
    suffix = Path(original_name).suffix
    safe_name = f"{Path(original_name).stem}-{uuid4().hex[:12]}{suffix}"
    file_path = UPLOAD_DIR / safe_name

    total = 0
    with open(file_path, "wb") as buffer:
        while chunk := file.file.read(1024 * 1024):
            total += len(chunk)
            if total > MAX_UPLOAD_BYTES:
                file_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Resume exceeds the maximum allowed size.")
            buffer.write(chunk)

    return str(file_path)


def upload_resume(file: UploadFile):
    if not file.filename or Path(file.filename).suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF file.")

    file_path = save_uploaded_file(file)

    try:
        with open(file_path, "rb") as uploaded:
            if uploaded.read(5) != b"%PDF-":
                file_path_obj = Path(file_path)
                file_path_obj.unlink(missing_ok=True)
                raise HTTPException(status_code=400, detail="Invalid PDF file signature.")
        ingest_resume(file_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Resume ingestion failed.") from exc

    return {"message": "Resume uploaded and ingested successfully.", "file_path": file_path}
