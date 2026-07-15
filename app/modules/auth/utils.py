from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt  # <--- Dùng thẳng thư viện này
from jose import jwt

from app.config import settings
from app.modules.auth.schemas import TokenPayload


def hash_password(password: str) -> str:
    """Băm mật khẩu an toàn, tương thích tuyệt đối với Python 3.12"""
    # Sinh muối (salt) ngẫu nhiên
    salt = bcrypt.gensalt()
    # Mã hóa chuỗi password dạng chuỗi (utf-8) sang bytes rồi tiến hành băm
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    # Trả về dạng chuỗi định dạng str để lưu vào Database
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kiểm tra mật khẩu khớp"""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def create_jwt_token(subject: Any, expires_delta: timedelta, token_type: str) -> str:
    """Hàm chung để sinh ra chuỗi Access Token hoặc Refresh Token"""
    expire = datetime.now(UTC) + expires_delta
    to_encode = {
        "sub": str(subject),
        "exp": int(expire.timestamp()),
        "type": token_type,
    }
    encoded_jwt = jwt.encode(
        to_encode, settings.APP_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return str(encoded_jwt)


def decode_jwt_token(token: str) -> TokenPayload | None:
    """Hàm decode jwt token và return user id"""
    try:
        payload = jwt.decode(
            token, settings.APP_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str | None = payload.get("sub")
        exp: int = payload.get("exp", 0)
        return TokenPayload(sub=user_id, exp=exp)
    except Exception:
        return None
