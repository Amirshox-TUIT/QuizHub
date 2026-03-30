from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.core.dependencies import get_db
from src.models.quiz import Quiz
from src.models.question import Question
from src.models.answer import Answer
from src.schemas.question import QuestionCreate, QuestionRead
from src.schemas.answer import AnswerCreate


class QuestionEndpoints:
    def __init__(self) -> None:
        self.router = APIRouter(prefix="/question", tags=["question"])
        self.router.post("/", response_model=QuestionRead)(self.add_question)

    async def add_question(
        self,
        question_data: QuestionCreate,
        answers: list[AnswerCreate],
        db: AsyncSession = Depends(get_db)
    ):
        result = await db.execute(select(Quiz).where(Quiz.id == question_data.quiz_id))
        quiz = result.scalar_one_or_none()
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        question = Question(title=question_data.title, quiz_id=question_data.quiz_id)
        db.add(question)
        await db.flush()

        for answer_data in answers:
            answer = Answer(
                title=answer_data.title,
                is_true_answer=answer_data.is_true_answer,
                question_id=question.id
            )
            db.add(answer)

        await db.commit()
        await db.refresh(question)

        return question
