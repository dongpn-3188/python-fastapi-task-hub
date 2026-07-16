from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_id
from app.database import get_db
from app.modules.users.schemas import (
    UserChangePassword,
    UserResponse,
    UserUpdate,
)
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["User"])

@router.get(
    "/me", response_model=UserResponse, status_code=status.HTTP_200_OK
)
async def get_me(
    current_user_id: str = Depends(get_current_user_id), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> UserResponse:
    """Endpoint lấy thông tin user hiện tại"""
    user_service = UserService(db)
    info_user = await user_service.get_user(current_user_id)
    return UserResponse.model_validate(info_user)

@router.patch(
    "/me", response_model=UserResponse, status_code=status.HTTP_200_OK
)
async def patch_me(
    user_data: UserUpdate,
    current_user_id: str = Depends(get_current_user_id), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> UserResponse:
    """Endpoint để cập nhật thông tin user"""
    user_service = UserService(db)
    updated_user = await user_service.update_user(current_user_id, user_data)
    return UserResponse.model_validate(updated_user)

@router.post(
    "/change-password", status_code=status.HTTP_204_NO_CONTENT
)
async def change_password(
    data: UserChangePassword,
    current_user_id: str = Depends(get_current_user_id), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
) -> None:
    """Endpoint để cập nhật thông tin user"""
    user_service = UserService(db)
    await user_service.change_password(current_user_id, data)
    return None
