from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.init_db import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    quizzes = relationship("Quiz", back_populates="author")
    user_answers = relationship("UserAnswer", back_populates="user")
    profile = relationship(
        "Profile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    quizzes_progress = relationship("UserQuizProgress", back_populates="user", cascade="all, delete-orphan")


class Profile(BaseModel):
    __tablename__ = "profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    bio: Mapped[str] = mapped_column(String(100), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )
    user = relationship("User", back_populates="profile")
