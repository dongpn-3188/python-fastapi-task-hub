from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.utils import hash_password, verify_password
from app.modules.users.models import User, UserRole
from app.modules.users.schemas import (
    UserChangePassword,
    UserCreate,
    UserUpdate,
)


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_data: UserCreate) -> User:
        """Logic xử lý đăng ký tài khoản người dùng mới"""
        result = await self.db.execute(
            select(User).where(User.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email này đã được đăng ký trong hệ thống",
            )

        hashed_pwd = hash_password(user_data.password)
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_pwd,
            full_name=user_data.full_name,
            is_active=True,
        )

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        return new_user

    async def get_user(self, user_id: str) -> User:
        """Logic lấy thông tin user đang đăng nhập"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        info_user = result.scalar_one_or_none()

        if info_user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không tìm thấy user",
            )

        return info_user

    async def update_user(
        self,
        current_user_id: str,
        target_user_id: str,
        user_data: UserUpdate
    ) -> User:
        """Logic cập nhật thông tin user"""
        login_user = await self.get_user(current_user_id)

        update_data = user_data.model_dump(exclude_unset=True)

        if login_user.role != UserRole.ADMIN:
            admin_fields = {"password", "role", "is_active"}

            if any(field in update_data for field in admin_fields):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Không có quyền thay đổi thông tin này"
                )

        need_update_user = await self.get_user(target_user_id)

        if "password" in update_data and update_data["password"]:
            update_data["password"] = hash_password(update_data["password"])

        for key, value in update_data.items():
            setattr(need_update_user, key, value)

        self.db.add(need_update_user)
        await self.db.commit()

        await self.db.refresh(need_update_user)

        return need_update_user


    async def change_password(
        self, current_user_id: str, data: UserChangePassword
    ) -> None:
        """Logic thay đổi mật khẩu"""

        user = await self.get_user(current_user_id)

        if not verify_password(data.old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mật khẩu cũ không chính xác"
            )

        user.hashed_password = hash_password(data.new_password)

        self.db.add(user)
        await self.db.commit()
        return None

    async def verify_admin_access(self, current_user_id: str) -> bool:
        user = await self.get_user(current_user_id)
        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chỉ Admin mới có quyền thực hiện hành động này"
            )

        return True
