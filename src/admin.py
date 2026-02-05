from sqladmin import Admin

from src.admin.answer import AnswerAdmin
from src.admin.question import QuestionAdmin
from src.admin.quiz import QuizAdmin
from src.admin.user import UserAdmin, ProfileAdmin, UserAnswerAdmin, UserQuizProgressAdmin
from src.db.session import engine

def setup_admin(app):
    admin = Admin(app, engine)

    admin.add_view(UserAdmin)
    admin.add_view(ProfileAdmin)
    admin.add_view(QuizAdmin)
    admin.add_view(QuestionAdmin)
    admin.add_view(AnswerAdmin)
    admin.add_view(UserAnswerAdmin)
    admin.add_view(UserQuizProgressAdmin)
