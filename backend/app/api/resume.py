from fastapi import APIRouter, File, UploadFile
from app.services.resume_service import upload_resume

router = APIRouter(prefix="/resume", tags=["Resume"])    

@router.post("/upload_resume")
def upload_resume_endpoint(file: UploadFile = File(...)):
    return upload_resume(file)




