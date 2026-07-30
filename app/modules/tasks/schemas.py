import uuid
from typing import Self

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.modules.tasks.models import TaskStatus, TaskPriority

class TaskResponse(BaseModel):
    """Dữ liệu trả về thông tin Task"""

    id: uuid.UUID

    model_config = {
        "from_attributes": True
    }
