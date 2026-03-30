from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.admin import setup_admin

from src.api.routers import main_router

app = FastAPI(title="QuizHub")

app.include_router(main_router, prefix="/api")

setup_admin(app)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



