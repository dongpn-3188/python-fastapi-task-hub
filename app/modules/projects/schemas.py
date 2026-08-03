from pydantic import BaseModel, Field

from app.modules.common.schemas import ProjectBasicInfo
from app.modules.projects.models import ProjectStatus
from app.modules.tasks.schemas import TaskResponse


class ProjectCreate(BaseModel):
    """Dữ liệu khởi tạo project mới trong workspace"""

    name: str = Field(..., min_length=1, description="Tên của project")
    description: str | None = Field(
        default=None, max_length=200, description="Mô tả project"
    )

class ProjectUpdate(BaseModel):
    """Dữ liệu cập nhật của project"""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Tên của project"
    )
    description: str | None = Field(
        default=None,
        max_length=200,
        description="Mô tả project"
    )

    status: ProjectStatus | None = Field(
        default=None,
        description="Trạng thái của project"
    )


class PageInfo(BaseModel):
    """Dữ liệu phân trang"""
    page_number: int
    page_size: int
    total_items: int


class TaskList(BaseModel):
    """Dữ liệu danh sách Task đã phân trang"""

    data: list[TaskResponse] = Field(default_factory=list)
    page: PageInfo



class ProjectResponse(ProjectBasicInfo):
    """Dữ liệu trả về thông tin chi tiết Project"""

    tasks: TaskList


