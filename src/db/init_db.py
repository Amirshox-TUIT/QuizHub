from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, DateTime

from src.db.base import Base


class BaseModel(Base):
    __abstract__ = True
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )