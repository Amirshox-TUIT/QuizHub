from pydantic import BaseModel, Field


class AnswerRead(BaseModel):
    id: int
    title: str

    model_config = {
        "from_attributes": True
    }


class AnswerCreate(BaseModel):
    question_id: int
    title: str
    is_true_answer: bool = Field(default=False)


class AnswerSubmit(BaseModel):
    question_id: int
    answer_id: int

class AnswersResult(BaseModel):
    answers: list[AnswerSubmit]
    total_time: int