import uuid
from typing import Self

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.modules.users.models import UserRole


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
    role: str

    model_config = {
        "from_attributes": True
    }

class UserUpdate(BaseModel):
    """Dữ liệu để cập nhật thông tin user"""

    email: EmailStr | None = Field(
        default=None,
        description="Địa chỉ email mới"
    )
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100, description="Họ và tên đầy đủ"
    )

    model_config = {
        "from_attributes": True
    }

class UserUpdateAdmin(UserUpdate):
    """Dữ liệu để cập nhật thông tin user"""

    password: str | None = Field(
        default=None,
        min_length=6,
        description="Mật khẩu từ 6 ký tự trở lên"
    )
    is_active: bool | None = Field(
        default=None,
        description="Trạng thái tài khoản"
    )
    role: UserRole | None=Field(
        default=None,
        description="Quyền hạn của user"
    )

class UserChangePassword(BaseModel):
    """Dữ liệu để đổi mật khẩu user"""

    old_password: str = Field(
        min_length=6,
        description="Mật khẩu từ 6 ký tự trở lên"
    )
    new_password: str = Field(
        min_length=6,
        description="Mật khẩu từ 6 ký tự trở lên"
    )
    confirm_password: str = Field(
        min_length=6,
        description="Nhập lại mật khẩu mới để xác nhận"
    )

    @model_validator(mode="after")
    def verify_password_match(self) -> Self:
        """Kiểm tra mật khẩu mới và mật khẩu xác nhận có khớp nhau không"""
        if self.new_password != self.confirm_password:
            raise ValueError("Mật khẩu xác nhận không khớp với mật khẩu mới")
        return self
