import uuid

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Dữ liệu đầu vào khi client đăng ký tài khoản mới"""

    email: EmailStr
    password: str = Field(..., min_length=6, description="Mật khẩu từ 6 ký tự trở lên")
    full_name: str = Field(
        ..., min_length=2, max_length=100, description="Họ và tên đầy đủ"
    )


class UserResponse(BaseModel):
    """Dữ liệu an toàn trả về cho Client sau khi đăng ký thành công"""

    id: uuid.UUID
    email: EmailStr
    full_name: str
    is_active: bool

    class Config:
        from_attributes = True  # Giúp Pydantic hiểu và parse được từ SQLAlchemy Model
