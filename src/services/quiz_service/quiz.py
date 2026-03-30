import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.dependencies import get_db, get_current_user
from src.core.redis_config import redis
from src.models import Quiz, UserQuizProgress, Question, Answer, User
from src.models.answer import UserAnswer
from src.schemas.answer import AnswersResult
from src.schemas.question import QuestionStart
from src.schemas.quiz import QuizReadSchema, QuizCreateSchema, QuizStartSchema


class QuizEndpoints:
    def __init__(self) -> None:
        self.router = APIRouter(prefix="/quizzes", tags=["quiz"])
        self.router.get("/recommended", response_model=list[QuizReadSchema])(self.get_quiz)
        self.router.post("/", response_model=QuizReadSchema)(self.create_quiz)
        self.router.post("/upload")(self.create_quiz_from_file)
        self.router.get("/{quiz_uuid}/start", response_model=QuizStartSchema)(self.start_quiz)
        self.router.post("/{quiz_uuid}/result")(self.submit_quiz_result)

    async def get_quiz(self, db: AsyncSession = Depends(get_db)):
        cache_key = "recommended:quizzes"

        cached = await redis.get(cache_key)
        if cached:
            return [QuizReadSchema(**q) for q in json.loads(cached)]

        result = await db.execute(
            select(func.count()).select_from(UserQuizProgress)
        )
        count = result.scalar_one()

        if count > 100:
            total_attempts = (
                select(
                    UserQuizProgress.quiz_id,
                    func.count(UserQuizProgress.id).label("attempts")
                )
                .group_by(UserQuizProgress.quiz_id)
                .cte("total_attempts")
            )

            total_finished = (
                select(
                    UserQuizProgress.quiz_id,
                    func.count(UserQuizProgress.id).label("finished")
                )
                .where(UserQuizProgress.finished.is_(True))
                .group_by(UserQuizProgress.quiz_id)
                .cte("total_finished")
            )

            score = func.coalesce(
                (total_finished.c.finished * 1.0) /
                func.nullif(total_attempts.c.attempts, 0),
                0
            )

            query = (
                select(Quiz)
                .join(total_attempts, total_attempts.c.quiz_id == Quiz.id)
                .outerjoin(total_finished, total_finished.c.quiz_id == Quiz.id)
                .where(Quiz.is_active.is_(True))
                .order_by(score.desc(), total_attempts.c.attempts.desc())
                .limit(10)
            )
        else:
            query = (
                select(Quiz)
                .where(Quiz.is_active.is_(True))
                .order_by(Quiz.created_at.desc())
                .limit(10)
            )

        result = await db.execute(query)
        quizzes = result.scalars().all()

        response = [QuizReadSchema.from_orm(q) for q in quizzes]

        encoded = jsonable_encoder(response)

        await redis.set(
            cache_key,
            json.dumps(encoded),
            ex=300
        )

        return response

    async def create_quiz(
            self,
            quiz_data: QuizCreateSchema,
            current_user=Depends(get_current_user),
            db: AsyncSession = Depends(get_db)
    ):
        quiz = Quiz(
            title=quiz_data.title,
            description=quiz_data.description,
            time_limit=quiz_data.time_limit,
            author_id=current_user.id
        )
        db.add(quiz)
        await db.commit()
        await db.refresh(quiz)

        return quiz

    async def create_quiz_from_file(
            self,
            file: UploadFile = File(...),
            current_user=Depends(get_current_user),
    ):
        tmp_path = f"/tmp/{file.filename}"
        with open(tmp_path, "wb") as f:
            f.write(await file.read())

        from src.utils.celery_tasks import create_quiz_from_file_task
        create_quiz_from_file_task.delay(tmp_path, current_user.id)

        return {"message": "File received, quiz creation in progress"}

    async def start_quiz(
            self,
            quiz_uuid: str,
            current_user=Depends(get_current_user),
            db: AsyncSession = Depends(get_db)
    ):
        quiz_cache_key = f"quiz:data:{quiz_uuid}"
        cache = await redis.get(quiz_cache_key)
        if cache:
            quiz_data = QuizStartSchema(**json.loads(cache))
        else:
            result = await db.execute(
                select(Quiz)
                .where(Quiz.uuid == quiz_uuid)
                .options(
                    selectinload(Quiz.questions)
                    .selectinload(Question.answers)
                )
            )
            quiz = result.scalars().one_or_none()
            if not quiz:
                raise HTTPException(status_code=404, detail="Quiz not found")

            quiz_data = QuizStartSchema(
                uuid=quiz.uuid,
                title=quiz.title,
                author_id=quiz.author_id,
                description=quiz.description,
                questions=[QuestionStart.from_orm(q) for q in quiz.questions],
            )

            await redis.set(
                quiz_cache_key,
                json.dumps(quiz_data.dict()),
                ex=600
            )

        result = await db.execute(
            select(UserQuizProgress)
            .where(
                UserQuizProgress.quiz_id == quiz_data.uuid,
                UserQuizProgress.user_id == current_user.id
            )
        )
        exists = result.scalar_one_or_none()

        db.add_all([
            UserAnswer(user_id=current_user.id, question_id=q.id)
            for q in quiz_data.questions
        ])

        db.add(
            UserQuizProgress(
                quiz_id=quiz_data.uuid,
                user_id=current_user.id,
                start_time=datetime.utcnow(),
                first_attempt=not exists,
                total_questions=len(quiz_data.questions),
            )
        )

        await db.commit()

        return quiz_data

    async def submit_quiz_result(
            self,
            quiz_uuid: str,
            user_answers: AnswersResult,
            current_user=Depends(get_current_user),
            db: AsyncSession = Depends(get_db)
    ):
        result = await db.execute(
            select(UserQuizProgress)
            .where(
                and_(
                    UserQuizProgress.quiz_id == quiz_uuid,
                    UserQuizProgress.user_id == current_user.id
                )
            )
            .options(
                selectinload(UserQuizProgress.user)
                .selectinload(User.user_answers)
            )
        )
        quiz_progress = result.scalar_one_or_none()
        if not quiz_progress:
            raise HTTPException(status_code=404, detail="Quiz not found")

        quiz_progress.finished_at = quiz_progress.start_time + timedelta(seconds=user_answers.total_time)
        quiz_progress.total_time = user_answers.total_time

        answer_ids = [a.answer_id for a in user_answers.answers]
        result = await db.execute(select(Answer).where(Answer.id.in_(answer_ids)))
        answers_map = {a.id: a for a in result.scalars().all()}

        correct_count = 0
        skipped_count = 0
        for ua in quiz_progress.user_answers:
            submitted = next((a for a in user_answers.answers if a.question_id == ua.question_id), None)
            if submitted:
                answer = answers_map.get(submitted.answer_id)
                if not answer or answer.question_id != ua.question_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid answer for question {ua.question_id}"
                    )
                ua.answer_id = answer.id
                ua.is_skipped = False
                correct_count += int(answer.is_true_answer)
            else:
                skipped_count += 1
            db.add(ua)

        quiz_progress.correct_count = correct_count
        quiz_progress.skipped_count = skipped_count
        db.add(quiz_progress)
        await db.commit()
        await db.refresh(quiz_progress)

        position = await quiz_progress.get_user_position(db=db) if hasattr(quiz_progress, "get_user_position") else None

        return {
            "quiz_id": quiz_progress.quiz_id,
            "user_id": quiz_progress.user_id,
            "correct_count": correct_count,
            "skipped_count": skipped_count,
            "total_time": user_answers.total_time,
            "finished_at": quiz_progress.finished_at,
            "position": position
        }
