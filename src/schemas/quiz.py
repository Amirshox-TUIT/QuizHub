from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas.question import QuestionStart


class QuizCreateSchema(BaseModel):
    title: str
    description: Optional[str] = None
    time_limit: int = Field(30, ge=0, le=120)

class QuizReadSchema(BaseModel):
    id: int
    uuid: str
    title: str
    author_id: int
    description: str
    time_limit: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserQuizProgressRead(BaseModel):
    user_id: int
    quiz_id: str
    start_time: Optional[datetime] = None
    current_question_id: Optional[int] = None
    finished: bool = False
    total_time: int = 0
    first_attempt: bool = True
    position: Optional[int] = None
    correct_answers: int = 0

    model_config = {
        "from_attributes": True
    }

class UserQuizProgressUpdate(BaseModel):
    current_question_id: Optional[int] = None
    finished: Optional[bool] = None
    total_time: Optional[int] = None
    correct_answers: Optional[int] = None


class UserQuizProgressCreate(BaseModel):
    user_id: int
    quiz_id: str
    start_time: datetime = Field(default_factory=datetime.utcnow)
    first_attempt: bool = True


class QuizStartSchema(BaseModel):
    uuid: str
    title: str
    author_id: int
    description: Optional[str] = None
    questions: List[QuestionStart]

    model_config = {"from_attributes": True}
