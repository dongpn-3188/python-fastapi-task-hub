import json

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.modules.auth.utils import decode_jwt_token
from app.services.redis import (
    RedisClient,
    get_redis_client,
)

reusable_oauth2 = HTTPBearer(scheme_name="Authorization")


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(reusable_oauth2),  # noqa: B008
    redis_client: RedisClient = Depends(get_redis_client),  # noqa: B008
) -> str:
    """Dependency giải mã Access Token từ HTTPBearer và check Blocklist"""
    access_token = credentials.credentials

    token_data = decode_jwt_token(access_token)
    if not token_data or not token_data.sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = token_data.sub

    block_list_key = f"block_access_list:{user_id}"
    raw_block_data = await redis_client.get(block_list_key)

    if raw_block_data:
        try:
            block_dict = json.loads(raw_block_data)
            if access_token in block_dict:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token này đã bị vô hiệu hóa (Đã Đăng xuất)",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except Exception:
            pass

    return user_id
