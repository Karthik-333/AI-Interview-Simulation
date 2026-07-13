from fastapi import FastAPI
from app.api.interviews import router as interview_router
from app.api.resume import router as resume_router 


app = FastAPI()

app.include_router(interview_router)
app.include_router(resume_router)      
