from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.init_db import BaseModel


class Question(BaseModel):
    __tablename__ = "questions"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id"), nullable=False)
    quiz = relationship("Quiz", back_populates="questions")
    answers = relationship("Answer", back_populates="question")





