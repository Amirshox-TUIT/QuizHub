from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserSchemaCreate(BaseModel):
    username: str
    email: str
    password: str


class UserRead(BaseModel):
    id: int
    username: str

    model_config = {
        "from_attributes": True
    }


class ProfileUpdateCreate(BaseModel):
    bio: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class ProfileRead(BaseModel):
    username: str
    bio: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    avatar_url: Optional[str]

    model_config = {
        "from_attributes": True
    }


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class QuizStatsSchema(BaseModel):
    username: str
    total_attempts: int
    total_time: int
    correct_answers: int
    wrong_answers: int
    position: int
    skipped_count: int
    created_at: datetime


class ProfileStatsSchema(BaseModel):
    username: str
    quiz_stats: list[QuizStatsSchema]
    total_finished_attempts: int

