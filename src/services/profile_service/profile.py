import json
from bisect import bisect_right

from fastapi import APIRouter, HTTPException
from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.dependencies import get_db, get_current_user
from src.core.redis_config import redis
from src.models import User, Profile, Quiz, UserQuizProgress, Question
from src.schemas.user import ProfileRead, ProfileUpdateCreate, ProfileStatsSchema, QuizStatsSchema


class ProfileEndpoints:
    def __init__(self) -> None:
        self.router = APIRouter(prefix="/profile", tags=["profile"])
        self.router.get("/{username}", response_model=ProfileRead)(self.get_profile)
        self.router.patch("/me", response_model=ProfileUpdateCreate)(self.update_profile)
        self.router.get("/{username}/stats", response_model=ProfileStatsSchema)(self.get_stats)

    async def get_profile(self, username: str, db: AsyncSession = Depends(get_db)):
        cache_key = f"profile:{username}"
        user_profile = await redis.get(cache_key)
        if user_profile:
            return ProfileRead(**json.loads(user_profile))

        result = await db.execute(
            select(User)
            .where(User.username == username)
            .options(selectinload(User.profile)
                     ))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        profile = ProfileRead(
            username=user.username,
            bio=user.profile.bio,
            first_name=user.profile.first_name,
            last_name=user.profile.last_name,
            avatar_url=user.profile.avatar_url,
        )
        await redis.set(
            cache_key,
            json.dumps(profile.dict()),
            ex=300
        )
        return profile

    async def update_profile(
            self,
            profile_data: ProfileUpdateCreate,
            current_user=Depends(get_current_user),
            db: AsyncSession = Depends(get_db)
    ):
        result = await db.execute(select(Profile).where(Profile.user_id == current_user.id))
        profile = result.scalar_one_or_none()
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        profile_data = profile_data.dict(exclude_unset=True)
        for key, value in profile_data.items():
            setattr(profile, key, value)

        await db.commit()
        await db.refresh(profile)
        cache_key = f"profile:{current_user.username}"
        profile_dict = ProfileUpdateCreate.from_orm(profile).dict()
        await redis.set(cache_key, json.dumps(profile_dict), ex=300)
        return profile

    async def get_stats(self, username: str, db: AsyncSession = Depends(get_db)):
        cache_key = f"profile:stats:{username}"
        user_profile = await redis.get(cache_key)
        if user_profile:
            return ProfileStatsSchema(**json.loads(user_profile))

        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        result = await db.execute(
            select(UserQuizProgress)
            .where(UserQuizProgress.user_id == user.id)
            .order_by(UserQuizProgress.quiz_id, UserQuizProgress.created_at)
        )
        progresses = result.scalars().all()

        if not progresses:
            empty_stats = ProfileStatsSchema(
                username=user.username,
                quiz_stats=[],
                total_finished_attempts=0
            )
            await redis.set(
                cache_key,
                json.dumps(jsonable_encoder(empty_stats)),
                ex=300
            )
            return empty_stats

        attempts_by_quiz = {}
        total_finished_attempts = 0
        quiz_ids = set()
        for progress in progresses:
            quiz_ids.add(progress.quiz_id)
            attempts_by_quiz[progress.quiz_id] = attempts_by_quiz.get(progress.quiz_id, 0) + 1
            total_finished_attempts += int(bool(progress.finished))

        result = await db.execute(
            select(
                UserQuizProgress.user_id,
                UserQuizProgress.quiz_id,
                UserQuizProgress.correct_answers,
                UserQuizProgress.total_time,
            )
            .where(
                UserQuizProgress.quiz_id.in_(quiz_ids),
                UserQuizProgress.first_attempt.is_(True)
            )
        )
        first_attempts = result.all()
        first_attempts_by_quiz = {}
        for user_id, quiz_id, correct_answers, total_time in first_attempts:
            first_attempts_by_quiz.setdefault(quiz_id, []).append(
                (user_id, correct_answers or 0, total_time or 0)
            )

        quiz_stats = []
        for progress in progresses:
            correct_count = progress.correct_answers or 0
            skipped_count = progress.skipped_count or 0
            total_time = progress.total_time or 0

            total_questions = progress.total_questions or 0
            wrong_count = total_questions - correct_count - skipped_count
            if wrong_count < 0:
                wrong_count = 0


            quiz_stats.append(
                QuizStatsSchema(
                    username=user.username,
                    total_attempts=attempts_by_quiz[progress.quiz_id],
                    total_time=total_time,
                    correct_answers=correct_count,
                    wrong_answers=wrong_count,
                    position=progress.get_user_position(db),
                    skipped_count=skipped_count,
                    created_at=progress.created_at
                )
            )

        quiz_stats.sort(key=lambda s: s.created_at, reverse=True)
        profile_stats = ProfileStatsSchema(
            username=user.username,
            quiz_stats=quiz_stats,
            total_finished_attempts=total_finished_attempts
        )

        await redis.set(
            cache_key,
            json.dumps(jsonable_encoder(profile_stats)),
            ex=300
        )
        return profile_stats
