from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Schema cho dữ liệu đăng nhập đầu vào"""

    email: EmailStr
    password: str = Field(..., min_length=6, description="Mật khẩu tối thiểu 6 ký tự")


class TokenResponse(BaseModel):
    """Schema trả về cho Client khi đăng nhập thành công"""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class TokenPayload(BaseModel):
    """Schema giải mã (decode) từ JWT Token để sử dụng trong nội bộ hệ thống"""

    sub: str  # Thường lưu user_id dưới dạng chuỗi
    exp: int


class RefeshTokenRequest(BaseModel):
    """Schema để làm mới cặp Token"""

    refresh_token: str
