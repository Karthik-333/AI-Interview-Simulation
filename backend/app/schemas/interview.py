from pydantic import BaseModel

class InterviewRequest(BaseModel):
    user_name: str
class User(BaseModel):
    name: str
    age: int