from enum import Enum as PyEnum
from datetime import datetime
import uuid
from sqlalchemy import BigInteger, ForeignKey, String, DateTime, Enum, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID # Import UUID chuyên dụng cho Postgres
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class TaskStatus(PyEnum):
    """Task status enum"""
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"  
    IN_REVIEW = "IN_REVIEW"
    DONE = "DONE"  


class TaskPriority(PyEnum):
    """Task priority enum"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

class Task(Base):
    """Task model"""
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        server_default=text("gen_random_uuid()")
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"), 
        nullable=False
    )

    assignee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.TODO, nullable=False)
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", foreign_keys=[project_id])
    assignee = relationship("User", foreign_keys=[assignee_id])
    creator = relationship("User", foreign_keys=[created_by])


class Label(Base):
    """Label model"""
    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(primary_key=True)

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    color: Mapped[str] = mapped_column(String(7), nullable=False) 
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", foreign_keys=[project_id])

    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_project_label_name"),
    )

class TaskLabel(Base):
    """TaskLabel model"""
    __tablename__ = "task_labels"

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        primary_key=True
    )

    label_id: Mapped[int] = mapped_column(
        ForeignKey("labels.id", ondelete="CASCADE"),
        primary_key=True
    )

    task = relationship("Task", foreign_keys=[task_id])
    label = relationship("Label", foreign_keys=[label_id])


class TaskComment(Base):
    """TaskComment model"""
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False
    )

    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    content: Mapped[str] = mapped_column(String(1000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task = relationship("Task", foreign_keys=[task_id])
    author = relationship("User", foreign_keys=[author_id])