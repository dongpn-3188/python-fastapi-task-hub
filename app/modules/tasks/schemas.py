import uuid
from datetime import datetime
from enum import Enum as PyEnum

from pydantic import BaseModel, Field

from app.modules.tasks.models import TaskPriority, TaskStatus


class TaskResponse(BaseModel):
    """Dữ liệu trả về thông tin Task"""

    id: uuid.UUID

    model_config = {
        "from_attributes": True
    }

class FilterField(PyEnum):
    """Field filter enum"""

    ASSIGNEE = "ASSIGNEE"
    TITLE = "TITLE"
    DESCRIPTION = "DESCRIPTION"
    STATUS = "STATUS"
    PRIORITY = "PRIORITY"
    DUE_DATE = "DUE_DATE"
    CREATE_BY = "CREATE_BY"
    CREATE_AT = "CREATE_AT"

class FilterMethod(PyEnum):
    """Field filter option"""

    IS = "IS"
    IS_NOT = "IS_NOT"
    CONTAIN = "CONTAIN"
    DOESNT_CONTAIN = "DOESNT_CONTAIN"
    GREATER = "GREATER"
    LESS = "LESS"

class FilterOption(BaseModel):
    """Dữ liệu filter"""

    field: FilterField
    method: FilterMethod
    value: str

class TaskFilterRequest(BaseModel):
    """Dữ liệu filter danh sách Task"""

    filter: list[FilterOption] = Field(default_factory=list)
    page: int = Field(
        default=1, ge=1, description="Trang hiện tại, tối thiểu là 1"
    )
    size: int = Field(
        default=20, ge=1, le=100, description="Kích thước trang, tối đa 100"
    )

class TaskBaseRequest(BaseModel):
    """Dữ liệu dùng chung cho 2 request"""

    assignee_id: uuid.UUID | None = Field(
        default=None, description="id của member thực hiện"
    )
    description: str | None = Field(
        default=None, max_length=200, description="Mô tả task"
    )
    due_date: datetime | None = Field(
        default=None, description="Hạn cuối của Task"
    )

class CreateTaskRequest(TaskBaseRequest):
    """Dữ liệu tạo task mới trong project"""

    title: str = Field(
        max_length=200, description="tiêu đề của task"
    )
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM, description="mức độ ưu tiên của Task"
    )

class UpdateTaskRequest(TaskBaseRequest):
    """Dữ liệu cập nhật task (Mọi trường đều optional)"""

    title: str | None = Field(
        default=None, max_length=200, description="tiêu đề của task"
    )
    priority: TaskPriority | None = Field(
        default=None, description="mức độ ưu tiên của Task"
    )
    status: TaskStatus | None = Field(
        default=None, description="trạng thái của Task"
    )
