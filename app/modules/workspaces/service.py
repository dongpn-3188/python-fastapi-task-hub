import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.users.models import User
from app.modules.workspaces.models import Workspace, WorkspaceMember, WorkspaceRole
from app.modules.workspaces.schemas import (
    UserInfo,
    WorkspaceMembersRequest,
    WorkspaceResponse,
)


class WorkspaceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_owner_id(self, workspace_id: str) -> uuid.UUID:
        stmt_owner = select(Workspace.owner_id).where(Workspace.id == workspace_id)
        result_owner = await self.db.execute(stmt_owner)
        owner_id = result_owner.scalar_one_or_none()

        if owner_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace không tồn tại"
            )

        return owner_id

    async def _upsert_workspace_members(
        self, workspace_id: str, members_data: WorkspaceMembersRequest
    ) -> tuple[set[uuid.UUID], set[uuid.UUID]]:
        """Logic thêm mới hoặc cập nhật thành viên nếu đã có"""

        owner_id = await self.get_owner_id(workspace_id)

        req_map = {
            item.user_id: item.role
            for item in members_data.members
            if item.role != WorkspaceRole.OWNER and str(item.user_id) != str(owner_id)
        }
        req_user_ids = set(req_map.keys())

        if not req_user_ids:
            return set(), set(item.user_id for item in members_data.members)

        stmt = select(User.id).where(User.id.in_(req_user_ids))
        result = await self.db.execute(stmt)
        valid_user_ids = set(result.scalars().all())

        values_to_insert = [
            {
                "workspace_id": workspace_id,
                "user_id": uid,
                "role": req_map[uid],
            }
            for uid in valid_user_ids
        ]

        if not values_to_insert:
            return set(), req_user_ids

        insert_stmt = insert(WorkspaceMember).values(values_to_insert)
        upsert_stmt = insert_stmt.on_conflict_do_update(
            constraint="uq_workspace_user",
            set_=dict(
                role = insert_stmt.excluded.role,
                deleted_at = None
            ),
            where=(WorkspaceMember.role != WorkspaceRole.OWNER)
        )

        await self.db.execute(upsert_stmt)
        await self.db.commit()

        return valid_user_ids, req_user_ids - valid_user_ids

    async def check_permission(
        self, workspace_id: str, user_id: str,
        min_role: WorkspaceRole = WorkspaceRole.VIEWER
    ) -> None:
        """Logic kiểm tra quyền hạn của user trong workspace"""

        result = await self.db.execute(
            select(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.deleted_at.is_(None)
            )
        )

        current_user_member = result.scalar_one_or_none()

        not_permission = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền thực hiện thao tác này",
        )

        if current_user_member is None:
            raise not_permission

        match min_role:
            case WorkspaceRole.VIEWER:
                return None
            case WorkspaceRole.EDITOR:
                if current_user_member.role == WorkspaceRole.VIEWER:
                    raise not_permission
            case WorkspaceRole.OWNER:
                if current_user_member.role != WorkspaceRole.OWNER:
                    raise not_permission

    async def get_workspace_info(self, workspace_id:str) -> WorkspaceResponse:
        """Logic lấy thông tin workspace theo id"""

        self.db.expire_all()

        stmt_workspace = (
            select(Workspace)
            .where(Workspace.id == workspace_id)
            .options(selectinload(Workspace.owner))
        )
        result_workspace = await self.db.execute(stmt_workspace)
        workspace = result_workspace.scalar_one_or_none()

        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace không tồn tại")

        stmt_members = (
            select(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.deleted_at.is_(None),
            )
            .options(selectinload(WorkspaceMember.user))
        )
        result_members = await self.db.execute(stmt_members)
        active_members = list(result_members.scalars().all())

        members_info = [
            UserInfo.from_workspace_member(m) for m in active_members
        ]

        owner_member = next(
            (m for m in active_members if m.role == WorkspaceRole.OWNER), None
        )

        if not owner_member:
            raise HTTPException(
                status_code=500,
                detail="Dữ liệu Workspace bị lỗi: Không tìm thấy Owner"
            )

        owner_info = UserInfo.from_workspace_member(owner_member)

        return WorkspaceResponse(
            id=workspace.id,
            name=workspace.name,
            owner=owner_info,
            members=members_info
        )

    async def create_new_workspace(
        self, user_id: str, workspace_name:str
    ) -> WorkspaceResponse:
        """Logic thêm mới workspace"""

        result = await self.db.execute(
            select(Workspace).where(Workspace.name == workspace_name)
        )
        existing_workspace = result.scalar_one_or_none()

        if existing_workspace:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Đã có workspace này trong hệ thống",
            )

        new_workspace_id = uuid.uuid4()

        new_workspace = Workspace(
            id=new_workspace_id,
            name = workspace_name,
            owner_id = user_id,
        )

        new_workspace_member = WorkspaceMember(
            workspace_id = new_workspace_id,
            user_id = user_id,
            role= WorkspaceRole.OWNER,
        )

        self.db.add(new_workspace)
        self.db.add(new_workspace_member)
        await self.db.commit()

        return await self.get_workspace_info(str(new_workspace.id))

    async def add_members_to_workspace(
        self, workspace_id: str, members_data: WorkspaceMembersRequest
    ) -> dict[str, Any]:
        """Logic trả về kết quả thêm mới thành viên"""
        valid_ids, invalid_ids = await self._upsert_workspace_members(
            workspace_id, members_data
        )
        return {
            "message": f"Đã thêm thành công {len(valid_ids)} thành viên",
            "added_count": len(valid_ids),
            "ignored_user_ids": list(invalid_ids)
        }

    async def update_members_role(
        self, workspace_id: str, members_data: WorkspaceMembersRequest
    ) -> dict[str, Any]:
        """Logic trả về kết quả cập nhật thành viên"""
        valid_ids, invalid_ids = await self._upsert_workspace_members(
            workspace_id, members_data
        )
        return {
            "message": f"Đã cập nhật quyền cho {len(valid_ids)} thành viên",
            "updated_count": len(valid_ids),
            "not_found_user_ids": list(invalid_ids)
        }

    async def remove_member(self, workspace_id: str, user_id: str) -> None:
        """Logic xóa thành viên khỏi workspace"""

        owner_id = await self.get_owner_id(workspace_id)
        if str(user_id) == str(owner_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể xóa chủ sở hữu (Owner) khỏi Workspace"
            )

        stmt = (
            update(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.deleted_at.is_(None)  # Chỉ xóa nếu chưa bị xóa
            )
            .values(deleted_at=func.now())
            .returning(WorkspaceMember.id)
        )
        result = await self.db.execute(stmt)
        updated_id = result.scalar_one_or_none()
        if updated_id is None:
            raise HTTPException(
                status_code=404,
                detail="Thành viên không tồn tại trong Workspace"
            )

        await self.db.commit()
        return None
