import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_id
from app.database import get_db
from app.modules.projects.schemas import (
    ProjectBasicInfo,
    ProjectResponse,
    ProjectUpdate,
)
from app.modules.projects.service import ProjectService
from app.modules.tasks.schemas import CreateTaskRequest, TaskFilterRequest, TaskResponse
from app.modules.tasks.service import TaskService
from app.modules.workspaces.models import WorkspaceRole
from app.services.redis import RedisClientWrapper, get_redis_client

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

@router.post(
    "/{id}/tasks/search", response_model=ProjectResponse, status_code=status.HTTP_200_OK
)
async def get_project_detail(
    id: uuid.UUID,
    filter_data: TaskFilterRequest,
    current_user_id: str = Depends(get_current_user_id),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
    redis_client: RedisClientWrapper = Depends(get_redis_client), # noqa: B008
) -> ProjectResponse:
    """Endpoint lấy thông tin chi tiết project và task"""
    project_service = ProjectService(db)
    task_service = TaskService(db, redis_client)
    project_info = await project_service.get_project_basic_info(str(id))
    await project_service.check_permission(
        project_id=id,
        user_id=current_user_id
    )
    task_list = await task_service.get_task_list_by_filter(id, filter_data)
    return ProjectResponse(
        **project_info.model_dump(),
        tasks=task_list,
    )

@router.post(
    "/{id}/tasks", response_model=TaskResponse, status_code=status.HTTP_200_OK
)
async def create_new_task_in_project(
    id: uuid.UUID,
    create_data: CreateTaskRequest,
    current_user_id: str = Depends(get_current_user_id),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
    redis_client: RedisClientWrapper = Depends(get_redis_client), # noqa: B008
) -> TaskResponse:
    """Endpoint lấy thông tin chi tiết project và task"""
    project_service = ProjectService(db)
    task_service = TaskService(db, redis_client)
    await project_service.check_permission(
        project_id=id,
        user_id=current_user_id,
        min_role=WorkspaceRole.EDITOR
    )
    return await task_service.create_new_task(id, current_user_id, create_data)

