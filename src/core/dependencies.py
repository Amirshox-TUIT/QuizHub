from src.db.session import AsyncSessionLocal
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.security import verify_token
from src.models.user import User


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        payload = verify_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

