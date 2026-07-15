from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from redis import asyncio as aioredis

# 🌟 Chỉ định nghĩa kiểu generic phức tạp này khi MYPY quét lỗi
if TYPE_CHECKING:
    from redis.asyncio import Redis
    RedisClient = Redis[str]
else:
    RedisClient = aioredis.Redis


from app.config import settings


async def get_redis_client() -> AsyncGenerator[RedisClient, None]:
    client: RedisClient = aioredis.from_url(
        settings.redis_url, encoding="utf-8", decode_responses=True
    )
    try:
        yield client
    finally:
        await client.close()
