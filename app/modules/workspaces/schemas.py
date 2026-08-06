import uuid

from pydantic import BaseModel, Field, field_validator

from app.modules.common.schemas import ProjectBasicInfo, UserInfo
from app.modules.workspaces.models import WorkspaceRole


class WorkspaceCreate(BaseModel):
    """Dữ liệu đầu vào khởi tạo Workspace"""

    name: str = Field(
        ..., min_length=2, max_length=100, description="Tên của workspace"
    )

class WorkspaceResponse(BaseModel):
    """Dữ liệu trả về thông tin Workspace"""

    id: uuid.UUID
    name: str
    owner: UserInfo
    members: list[UserInfo] = Field(default_factory=list)
    projects: list[ProjectBasicInfo] = Field(default_factory=list)

    model_config = {
        "from_attributes": True
    }

class MemberItem(BaseModel):
    """Dữ liệu member cần thêm vào workspace"""

    user_id: uuid.UUID = Field(..., description="ID của user cần thêm")
    role: WorkspaceRole = Field(
        default=WorkspaceRole.VIEWER,
        description="Quyền trong workspace (Mặc định: VIEWER)"
    )

    @field_validator("role")
    @classmethod
    def validate_role_not_owner(cls, value: WorkspaceRole) -> WorkspaceRole:
        if value == WorkspaceRole.OWNER:
            raise ValueError("Không thể gán quyền OWNER")
        return value

class WorkspaceMembersRequest(BaseModel):
    """Danh sách member thêm vào workspace"""

    members: list[MemberItem] = Field(
        min_length=1,
        description="Danh sách object các thành viên cần thêm"
    )
