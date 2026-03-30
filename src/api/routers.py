from fastapi import APIRouter

from src.api.endpoints.question.question import question_router
from src.api.endpoints.quiz.quiz import quiz_router
from src.api.endpoints.user.auth import auth_router
from src.api.endpoints.user.profile import profile_router
from src.core.ws_config import ws_router

main_router = APIRouter()

main_router.include_router(profile_router)
main_router.include_router(auth_router)

main_router.include_router(quiz_router)
main_router.include_router(question_router)
main_router.include_router(ws_router)