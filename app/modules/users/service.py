from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.modules.auth.utils import hash_password
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate


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
