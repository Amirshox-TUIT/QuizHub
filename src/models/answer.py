from sqlalchemy import ForeignKey, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.init_db import BaseModel


class Answer(BaseModel):
    __tablename__ = "answers"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id"),
        nullable=False,
    )
    question = relationship("Question", back_populates="answers")
    is_true_answer: Mapped[bool] = mapped_column(Boolean, default=False)



class UserAnswer(BaseModel):
    __tablename__ = "user_answers"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)
    answer_id: Mapped[int] = mapped_column(ForeignKey("answers.id"), nullable=True)

    is_true_answer: Mapped[bool] = mapped_column(Boolean, default=False)
    is_skipped: Mapped[bool] = mapped_column(Boolean, default=True)

    user = relationship("User", back_populates="user_answers")
    question = relationship("Question")
    answer = relationship("Answer")

