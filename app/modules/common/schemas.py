import uuid

from pydantic import BaseModel, EmailStr

from app.modules.projects.models import ProjectStatus
from app.modules.workspaces.models import WorkspaceMember


class ProjectBasicInfo(BaseModel):
    """Dữ liệu thông tin cơ bản của project"""

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    status: ProjectStatus
    description: str | None = None

    model_config = {
        "from_attributes": True
    }

class UserInfo(BaseModel):
    """Dữ liệu của user trong workspace"""

    id: uuid.UUID
    email: EmailStr
    full_name: str
    workspace_role: str | None = None

    model_config = {
        "from_attributes": True
    }

    @classmethod
    def from_workspace_member(cls, member: "WorkspaceMember") -> "UserInfo":
        """Map trực tiếp từ đối tượng WorkspaceMember của SQLAlchemy"""

        return cls(
            id=member.user.id,
            email=member.user.email,
            full_name=member.user.full_name,
            workspace_role=member.role
        )
