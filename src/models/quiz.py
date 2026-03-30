from datetime import datetime
import uuid


from sqlalchemy import ForeignKey, String, Boolean, select, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.init_db import BaseModel


class Quiz(BaseModel):
    __tablename__ = "quizzes"

    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
        server_default="gen_random_uuid()"
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    author = relationship("User", back_populates="quizzes")
    title: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )
    time_limit: Mapped[int] = mapped_column(Integer, default=30)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    users_progress = relationship("UserQuizProgress", back_populates="quiz", cascade="all, delete-orphan")

    def summary(self) -> str:
        return f"{self.title} ({len(self.questions)} questions)"


class UserQuizProgress(BaseModel):
    __tablename__ = "user_quiz_progress"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    quiz_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("quizzes.uuid"),
        nullable=False
    )

    start_time: Mapped[datetime | None] = mapped_column(nullable=True)
    current_question_id: Mapped[int | None] = mapped_column(ForeignKey("questions.id"), nullable=True)
    finished: Mapped[bool] = mapped_column(Boolean, default=False)
    total_time: Mapped[int | None] = mapped_column(nullable=True)
    first_attempt: Mapped[bool] = mapped_column(Boolean, default=True)
    user = relationship("User", back_populates="quizzes_progress")
    quiz = relationship("Quiz", back_populates="users_progress")
    correct_answers: Mapped[int] = mapped_column(
        Integer, nullable=True
    )
    skipped_count: Mapped[int] = mapped_column(
        Integer, nullable=True
    )
    total_questions: Mapped[int] = mapped_column(
        Integer, nullable=True
    )

    async def get_user_position(self, db: AsyncSession):
        stmt = select(UserQuizProgress).where(
            UserQuizProgress.quiz_id == self.quiz_id,
            UserQuizProgress.first_attempt == True,
        )
        result = await db.execute(stmt)
        progresses = result.scalars().all()

        leaderboard = []
        for p in progresses + [self]:

            leaderboard.append({
                "progress": p,
                "correct_answers": p.correct_answers,
                "total_time": p.total_time or 0
            })

        leaderboard.sort(key=lambda x: (-x["correct_answers"], x["total_time"]))
        for idx, entry in enumerate(leaderboard, start=1):
            if entry["progress"].user_id == self.user_id:
                return idx