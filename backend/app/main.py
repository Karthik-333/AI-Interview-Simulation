from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agents import router as agent_router
from app.api.auth import router as auth_router
from app.api.interviews import router as interview_router
from app.api.mcp import router as mcp_router
from app.api.resume import router as resume_router


app = FastAPI(title="AI Interview Simulation", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(interview_router)
app.include_router(resume_router)
app.include_router(mcp_router)
app.include_router(agent_router)
