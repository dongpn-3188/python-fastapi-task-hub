# app/database.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Đặt thành True nếu bạn muốn hiển thị toàn bộ câu lệnh SQL log ở terminal khi dev
    future=True
)


SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Ngăn SQLAlchemy tự động refresh object sau khi commit (rất quan trọng với Async)
)

class Base(DeclarativeBase):
    pass