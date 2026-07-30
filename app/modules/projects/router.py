import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_id
from app.database import get_db
from app.modules.projects.models import ProjectStatus
from app.modules.projects.schemas import (
    ProjectBasicInfo,
    ProjectUpdate,
)
from app.modules.projects.service import ProjectService
from app.modules.workspaces.models import WorkspaceRole
from app.modules.workspaces.service import WorkspaceService

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.patch(
    "/{id}", response_model=ProjectBasicInfo, status_code=status.HTTP_200_OK
)
async def update_project(
    id: uuid.UUID,
    project_data: ProjectUpdate,
    current_user_id: str = Depends(get_current_user_id),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> ProjectBasicInfo:
    """Endpoint cập nhật thông tin project"""
    project_service = ProjectService(db)
    return await project_service.update_project(
        project_id=str(id),
        user_id=current_user_id,
        data=project_data,
    )
