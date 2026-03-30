from sqladmin import Admin, ModelView
from fastapi import FastAPI

from src.db.session import engine
from src.models.user import User, Profile
from src.models.quiz import Quiz, UserQuizProgress
from src.models.question import Question
from src.models.answer import Answer, UserAnswer


class UserAdmin(ModelView, model=User):
    column_list = ["id", "username", "email", "is_active", "is_superuser"]


class ProfileAdmin(ModelView, model=Profile):
    column_list = ["id", "user_id", "first_name", "last_name", "bio", "avatar_url"]


class QuestionAdmin(ModelView, model=Question):
    column_list = ["id", "title", "quiz_id"]


class AnswerAdmin(ModelView, model=Answer):
    column_list = ["id", "title", "question_id", "is_true_answer"]


class QuizAdmin(ModelView, model=Quiz):
    column_list = ["id", "uuid", "title", "author_id", "time_limit", "is_active"]


class UserAnswerAdmin(ModelView, model=UserAnswer):
    column_list = ["id", "user_id", "question_id", "answer_id", "is_true_answer", "is_skipped"]


class UserQuizProgressAdmin(ModelView, model=UserQuizProgress):
    column_list = ["id", "user_id", "quiz_id", "current_question_id", "correct_answers", "finished", "total_time"]


def setup_admin(app: FastAPI):
    admin = Admin(app, engine)

    admin.add_view(UserAdmin)
    admin.add_view(ProfileAdmin)
    admin.add_view(QuizAdmin)
    admin.add_view(QuestionAdmin)
    admin.add_view(AnswerAdmin)
    admin.add_view(UserAnswerAdmin)
    admin.add_view(UserQuizProgressAdmin)

    return admin
