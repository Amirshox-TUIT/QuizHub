from pydantic import BaseModel
from typing import Optional, List
from src.schemas.answer import AnswerRead


class QuestionCreate(BaseModel):
    title: str
    quiz_id: int


class QuestionRead(BaseModel):
    id: int
    title: str
    quiz_id: int
    answers: List[AnswerRead] = []

    model_config = {
        "from_attributes": True
    }


class QuestionProgressRead(BaseModel):
    id: int
    title: str
    quiz_id: int
    is_finished: bool
    is_answered_true: Optional[bool] = None
    is_skipped: Optional[bool] = None

    model_config = {
        "from_attributes": True
    }

class QuestionStart(BaseModel):
    id: int
    title: str
    answers: List[AnswerRead]

    model_config = {"from_attributes": True}
