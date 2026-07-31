import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_id
from app.database import get_db
from app.modules.tasks.schemas import TaskResponse, UpdateTaskRequest
from app.modules.tasks.service import TaskService
from app.services.redis import RedisClientWrapper, get_redis_client

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.patch(
    "/{id}", response_model=TaskResponse, status_code=status.HTTP_200_OK
)
async def update_task_by_id(
    id: uuid.UUID,
    update_data: UpdateTaskRequest,
    current_user_id: str = Depends(get_current_user_id),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
    redis_client: RedisClientWrapper = Depends(get_redis_client), # noqa: B008
) -> TaskResponse:
    """Endpoint lấy thông tin chi tiết project và task"""
    task_service = TaskService(db, redis_client)
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
    task_service = TaskService(db, redis_client)
    await task_service.delete_task(id, current_user_id)

