from pydantic import BaseModel, HttpUrl, EmailStr
from typing import Any

class QuizTask(BaseModel):
    email: EmailStr
    secret: str
    url: HttpUrl

class Submission(BaseModel):
    email: str
    secret: str
    url: str
    answer: Any