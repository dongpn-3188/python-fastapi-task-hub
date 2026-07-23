from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import reusable_oauth2
from app.database import get_db
from app.modules.auth.schemas import LoginRequest, RefeshTokenRequest, TokenResponse
from app.modules.auth.service import AuthService
from app.modules.users.schemas import UserCreate, UserResponse
from app.modules.users.service import UserService
from app.services.redis import RedisClient, get_redis_client

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db), # noqa: B008
    redis_client: RedisClient = Depends(get_redis_client), # noqa: B008
) -> TokenResponse:
    """Endpoint xử lý đăng nhập trả về Access và Refresh Token"""
    auth_service = AuthService(db, redis_client)
    return await auth_service.authenticate_user(login_data)


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: UserCreate, db: AsyncSession = Depends(get_db) # noqa: B008
) -> UserResponse:
    """Endpoint xử lý Đăng ký tài khoản người dùng mới"""
    user_service = UserService(db)
    created_user = await user_service.create_user(user_data)
    return UserResponse.model_validate(created_user)


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh(
    refresh_data: RefeshTokenRequest,
    db: AsyncSession = Depends(get_db), # noqa: B008
    redis_client: RedisClient = Depends(get_redis_client), # noqa: B008
) -> TokenResponse:
    """Endpoint để làm mới cặp token cho user"""
    auth_service = AuthService(db, redis_client)
    return await auth_service.refresh_user_token(refresh_data.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(reusable_oauth2), # noqa: B008
    db: AsyncSession = Depends(get_db), # noqa: B008
    redis_client: RedisClient = Depends(get_redis_client), # noqa: B008
) -> None:
    """Endpoint để logout user"""
    auth_service = AuthService(db, redis_client)
    await auth_service.logout_user(credentials.credentials)
    return None
