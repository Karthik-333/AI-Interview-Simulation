from fastapi import FastAPI
from pydantic import BaseModel

app=FastAPI()

class InterviewRequest(BaseModel):
    user_name: str
class User(BaseModel):
    name: str
    age: int

@app.get("/")
def home():
    return {
        "message" : "Welcome to AI Interview Stimulation"
    }
@app.get("/health")
def health():
    return {
        "status" : "Healthy"
    }
@app.post("/interview/start")
def start_interview(request: InterviewRequest):
    return {
        "message": f"Interview started for {request.user_name}"
    }
@app.post("/test")
def test(user:User):
    return user

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {
        "user_id": user_id
    }