import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_id
from app.database import get_db
from app.modules.workspaces.models import WorkspaceRole
from app.modules.workspaces.schemas import (
    WorkspaceCreate,
    WorkspaceMembersRequest,
    WorkspaceResponse,
)
from app.modules.workspaces.service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

@router.post(
    "", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED
)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    current_user_id: str = Depends(get_current_user_id), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> WorkspaceResponse:
    """Endpoint tạo workspace mới"""
    workspace_service = WorkspaceService(db)
    return await workspace_service.create_new_workspace(
        current_user_id, workspace_data.name
    )

@router.get(
    "/{id}", response_model=WorkspaceResponse, status_code=status.HTTP_200_OK
)
async def get_workspace(
    id: uuid.UUID,
    current_user_id: str = Depends(get_current_user_id), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> WorkspaceResponse:
    """Endpoint lấy thông tin workspace"""
    workspace_service = WorkspaceService(db)
    await workspace_service.check_permission(str(id), current_user_id)
    return await workspace_service.get_workspace_info(str(id))

@router.post(
    "/{id}/members", status_code=status.HTTP_200_OK
)
async def add_members(
    id: uuid.UUID,
    members_data: WorkspaceMembersRequest,
    current_user_id: str = Depends(get_current_user_id), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> dict[str, Any]:
    """Endpoint thêm thành viên vào workspace"""
    workspace_service = WorkspaceService(db)
    await workspace_service.check_permission(
        str(id), current_user_id, WorkspaceRole.EDITOR
    )
    return await workspace_service.add_members_to_workspace(str(id), members_data)

@router.patch(
    "/{id}/members", status_code=status.HTTP_200_OK
)
async def edit_members(
    id: uuid.UUID,
    members_data: WorkspaceMembersRequest,
    current_user_id: str = Depends(get_current_user_id), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> dict[str, Any]:
    """Endpoint thay đổi quyền hạn thành viên"""
    workspace_service = WorkspaceService(db)
    await workspace_service.check_permission(
        str(id), current_user_id, WorkspaceRole.EDITOR
    )
    return await workspace_service.update_members_role(str(id), members_data)

@router.delete(
    "/{id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_members(
    id: uuid.UUID,
    user_id: uuid.UUID,
    current_user_id: str = Depends(get_current_user_id), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> None:
    """Endpoint xóa thành viên khỏi workspace"""
    workspace_service = WorkspaceService(db)
    await workspace_service.check_permission(
        str(id), current_user_id, WorkspaceRole.EDITOR
    )
    await workspace_service.remove_member(str(id), str(user_id))
    return None
