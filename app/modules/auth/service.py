import json
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.modules.auth.schemas import LoginRequest, TokenResponse
from app.modules.auth.utils import create_jwt_token, decode_jwt_token, verify_password
from app.modules.users.models import User
from app.services.redis import RedisClient


class AuthService:
    def __init__(self, db: AsyncSession, redis: RedisClient):
        self.db = db
        self.redis = redis

    async def authenticate_user(self, login_data: LoginRequest) -> TokenResponse:
        """Logic kiểm tra đăng nhập, sinh token và lưu phiên vào Redis"""

        result = await self.db.execute(
            select(User).where(User.email == login_data.email)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email hoặc mật khẩu không chính xác",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await self.generate_token_from_user(user)

    async def refresh_user_token(self, refresh_token: str) -> TokenResponse:
        """Logic refesh để lấy cặp token mới"""
        token_data = decode_jwt_token(refresh_token)

        if token_data is None:
            raise HTTPException(status_code=400, detail="Token không chính xác")

        user_id = token_data.sub
        if user_id is None:
            raise HTTPException(status_code=400, detail="Token không chính xác")

        redis_key = f"refresh_token:{user_id}"
        cache_redis_token = await self.redis.get(redis_key)

        if refresh_token != cache_redis_token:
            raise HTTPException(status_code=400, detail="Token không chính xác")

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=400,
                detail="Token không chính xác",
            )

        return await self.generate_token_from_user(user)

    async def logout_user(self, access_token: str) -> None:
        """Logic logout user"""
        token_data = decode_jwt_token(access_token)

        if token_data is None:
            raise HTTPException(status_code=400, detail="Token không chính xác")

        user_id = token_data.sub
        if user_id is None:
            raise HTTPException(status_code=400, detail="Token không chính xác")

        # Xoá cache refresh token
        redis_key = f"refresh_token:{user_id}"
        await self.redis.delete(redis_key)

        # Get block list access token
        block_access_tokens_redis_key = f"block_access_list:{user_id}"
        raw_block_data = await self.redis.get(block_access_tokens_redis_key)
        block_dict: dict[str, int] = {}
        if raw_block_data:
            try:
                block_dict = json.loads(raw_block_data)
            except Exception:
                block_dict = {}

        # Kiểm tra block list và xóa các token đã hết hạn
        current_timestamp = int(datetime.now(UTC).timestamp())
        for token in list(block_dict.keys()):
            if block_dict[token] < current_timestamp:
                del block_dict[token]

        # Thêm access token hiện tại vào block list
        ttl_seconds = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

        block_dict[access_token] = current_timestamp + ttl_seconds
        # Set lại block list

        # Tự động clear cache khi token mới thêm hết hạn
        await self.redis.setex(
            block_access_tokens_redis_key, ttl_seconds, json.dumps(block_dict)
        )

        return None

    async def generate_token_from_user(self, user: User) -> TokenResponse:
        """Hàm chung để sinh cặp token từ user"""
        # Kiểm tra trạng thái tài khoản nếu cần (ví dụ: is_active)
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Tài khoản đã bị khóa")

        access_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_expires = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

        access_token = create_jwt_token(user.id, access_expires, token_type="access")
        refresh_token = create_jwt_token(user.id, refresh_expires, token_type="refresh")

        redis_key = f"refresh_token:{user.id}"
        await self.redis.setex(
            redis_key, int(refresh_expires.total_seconds()), refresh_token
        )

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
