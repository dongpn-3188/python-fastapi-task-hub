from enum import Enum as PyEnum
from datetime import datetime
import uuid
from sqlalchemy import String, Boolean, DateTime, Enum, func, text
from sqlalchemy.dialects.postgresql import UUID # Import UUID chuyên dụng cho Postgres
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class UserRole(PyEnum):
    """User roles enum"""
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class User(Base):
    """User model"""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.MEMBER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
