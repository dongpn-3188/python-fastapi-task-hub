import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_id
from app.database import get_db
from app.modules.projects.service import ProjectService
from app.modules.tasks.schemas import (
    CommentRequest,
    CommentResponse,
    TaskResponse,
    UpdateTaskRequest,
)
from app.modules.tasks.service import TaskService
from app.services.redis import RedisClientWrapper, get_redis_client

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.patch(
    "/{id}",
    response_model=TaskResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK
)
async def update_task_by_id(
    id: uuid.UUID,
    update_data: UpdateTaskRequest,
    current_user_id: str = Depends(get_current_user_id),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
    redis_client: RedisClientWrapper = Depends(get_redis_client), # noqa: B008
) -> TaskResponse:
    """Endpoint lấy thông tin chi tiết project và task"""
    project_service = ProjectService(db)
    task_service = TaskService(db, redis_client, project_service)
    return await task_service.update_task(id, current_user_id, update_data)

@router.delete(
    "/{id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_task_by_id(
    id: uuid.UUID,
    current_user_id: str = Depends(get_current_user_id),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
    redis_client: RedisClientWrapper = Depends(get_redis_client), # noqa: B008
) -> None:
    """Endpoint lấy thông tin chi tiết project và task"""
    project_service = ProjectService(db)
    task_service = TaskService(db, redis_client, project_service)
    await task_service.delete_task(id, current_user_id)

@router.post(
    "/{id}/labels/{label_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def add_label_to_task(
    id: uuid.UUID,
    label_id: int,
    current_user_id: str = Depends(get_current_user_id),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
    redis_client: RedisClientWrapper = Depends(get_redis_client), # noqa: B008
) -> None:
    """Endpoint thêm label vào task"""
    project_service = ProjectService(db)
    task_service = TaskService(db, redis_client, project_service)
    await task_service.add_label(id, current_user_id, label_id)

@router.delete(
    "/{id}/labels/{label_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_label_from_task(
    id: uuid.UUID,
    label_id: int,
    current_user_id: str = Depends(get_current_user_id),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
    redis_client: RedisClientWrapper = Depends(get_redis_client), # noqa: B008
) -> None:
    """Endpoint xóa label khỏi task"""
    project_service = ProjectService(db)
    task_service = TaskService(db, redis_client, project_service)
    await task_service.remove_label(id, current_user_id, label_id)

@router.post(
    "/{id}/comments",
    response_model=CommentResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
)
async def add_comment_to_task(
    id: uuid.UUID,
    data: CommentRequest,
    current_user_id: str = Depends(get_current_user_id),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
    redis_client: RedisClientWrapper = Depends(get_redis_client), # noqa: B008
) -> CommentResponse:
    """Endpoint thêm comment vào task"""
    project_service = ProjectService(db)
    task_service = TaskService(db, redis_client, project_service)
    return await task_service.add_comment(id, current_user_id, data)

@router.patch(
    "/{id}/comments/{comment_id}",
    response_model=CommentResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
async def edit_comment_by_id(
    id: uuid.UUID,
    comment_id: int,
    data: CommentRequest,
    current_user_id: str = Depends(get_current_user_id),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
    redis_client: RedisClientWrapper = Depends(get_redis_client), # noqa: B008
) -> CommentResponse:
    """Endpoint sửa comment theo id"""
    project_service = ProjectService(db)
    task_service = TaskService(db, redis_client, project_service)
    return await task_service.edit_comment(id, current_user_id, comment_id, data)

@router.delete(
    "/{id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_comment_by_id(
    id: uuid.UUID,
    comment_id: int,
    current_user_id: str = Depends(get_current_user_id),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
    redis_client: RedisClientWrapper = Depends(get_redis_client), # noqa: B008
) -> None:
    """Endpoint xóa comment theo id"""
    project_service = ProjectService(db)
    task_service = TaskService(db, redis_client, project_service)
    await task_service.delete_comment(id, current_user_id, comment_id)
