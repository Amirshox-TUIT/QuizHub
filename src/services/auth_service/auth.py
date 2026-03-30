from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db
from src.core.security import create_access_token, create_refresh_token
from src.models import Profile
from src.models.user import User
from src.schemas.user import TokenSchema, UserSchemaCreate
from src.utils.hashing import hash_password, verify_password


class AuthEndpoints:
    def __init__(self) -> None:
        self.router = APIRouter(prefix="/auth", tags=["auth"])
        self.router.post("/register", response_model=TokenSchema)(self.register)
        self.router.post("/login", response_model=TokenSchema)(self.login)

    async def register(self, user_data: UserSchemaCreate, db: AsyncSession = Depends(get_db)):
        stmt = select(User).filter(or_(User.username == user_data.username, User.email == user_data.email))
        exist_user = await db.execute(stmt)
        if exist_user.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username or email already exists")

        hashed = hash_password(user_data.password)
        user = User(username=user_data.username, email=user_data.email, hashed_password=hashed)
        db.add(user)

        await db.flush()

        profile = Profile(user_id=user.id)
        db.add(profile)

        await db.commit()
        await db.refresh(user)
        await db.refresh(profile)

        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    async def login(self, user_data: UserSchemaCreate, db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(User).where(User.username == user_data.username))
        user = result.scalar_one_or_none()
        if not user or not verify_password(user_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
