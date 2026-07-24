import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Workspace(Base):
    """Workspace model"""

    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )

    # Đã liên kết khóa ngoại tới bảng users
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Quan hệ giúp lấy thông tin chủ sở hữu nhanh chóng
    owner = relationship("User", foreign_keys=[owner_id])


class WorkspaceRole(PyEnum):
    """Workspace roles enum"""

    OWNER = "OWNER"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"


class WorkspaceMember(Base):
    """Workspace member model"""

    __tablename__ = "workspace_members"

    id: Mapped[int] = mapped_column(primary_key=True)

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    role: Mapped[WorkspaceRole] = mapped_column(
        Enum(WorkspaceRole), default=WorkspaceRole.VIEWER, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    deleted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )

    # Quan hệ giúp lấy thông tin workspace và user nhanh chóng
    workspace = relationship("Workspace", foreign_keys=[workspace_id])
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),
    )
