from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from redis import asyncio as aioredis
from redis.asyncio.client import Pipeline

from app.config import settings

logger = logging.getLogger(__name__)

class DummyPipeline:
    """Dummy class nếu Redis sập, giúp code không bị AttributeError"""
    def set(self, *args: Any, **kwargs: Any) -> None: pass
    def get(self, *args: Any, **kwargs: Any) -> None: pass
    def delete(self, *args: Any, **kwargs: Any) -> None: pass
    async def execute(self) -> list[Any]: return []

class RedisClientWrapper:
    def __init__(self) -> None:
        self.client: aioredis.Redis[str] | None = None

    async def init(self) -> None:
        """Khởi tạo Singleton Connection Pool khi App Startup"""
        if not self.client:
            self.client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )

    async def close(self) -> None:
        """Đóng Connection Pool khi App Shutdown"""
        if self.client:
            await self.client.close()

    # ==================== HELPER WRAPPERS ====================

    async def safe_set(self, key: str, value: Any, ex: int | None = 86400) -> bool:
        """Ghi key an toàn, tự swallow exception nếu Redis lỗi"""
        if not self.client:
            return False
        try:
            await self.client.set(key, value, ex=ex)
            return True
        except Exception as e:
            logger.warning(f"Redis SET failed for key '{key}': {e}")
            return False

    async def safe_get(self, key: str) -> str | None:
        """Đọc key an toàn"""
        if not self.client:
            return None
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.warning(f"Redis GET failed for key '{key}': {e}")
            return None

    async def safe_delete(self, key: str) -> bool:
        """Xóa key an toàn"""
        if not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis DELETE failed for key '{key}': {e}")
            return False

    async def safe_mget(self, keys: list[str]) -> list[str | None]:
        """MGET an toàn"""
        if not self.client or not keys:
            return [None] * len(keys)
        try:
            return await self.client.mget(keys)
        except Exception as e:
            logger.warning(f"Redis MGET failed: {e}")
            return [None] * len(keys)

    @asynccontextmanager
    async def safe_pipeline(self) -> AsyncGenerator[
        Pipeline[str] | DummyPipeline, None
    ]:
        """Context manager bọc Pipeline an toàn.
        Nếu Redis lỗi lúc execute, trả về list rỗng thay vì raise Exception.
        """
        if not self.client:
            yield DummyPipeline()
            return

        pipe = self.client.pipeline()
        try:
            yield pipe
            await pipe.execute()
        except Exception as e:
            logger.warning(f"Redis Pipeline execution failed: {e}")
        finally:
            await pipe.close()

# Instance Singleton duy nhất dùng toàn app
redis_client = RedisClientWrapper()

def get_redis_client() -> RedisClientWrapper:
    return redis_client
