import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.projects.models import Project, ProjectStatus
from app.modules.projects.schemas import (
    PageInfo,
    ProjectBasicInfo,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    TaskList,
)
from app.modules.workspaces.models import WorkspaceMember, WorkspaceRole


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_project(
        self, project_id: str, user_id: str, data: ProjectUpdate
    ) -> ProjectBasicInfo:
        """Cập nhật project và kiểm tra quyền qua Subquery"""

        update_data = data.model_dump(exclude_unset=True)


        if not update_data:
            stmt_current = select(Project).where(Project.id == project_id)
            res = await self.db.execute(stmt_current)
            project = res.scalar_one_or_none()
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project không tồn tại",
                )
            return ProjectBasicInfo.model_validate(project)


        permission_subquery = (
            select(1)
            .select_from(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == Project.workspace_id,
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.role != WorkspaceRole.VIEWER,
                WorkspaceMember.deleted_at.is_(None),
            )
        )

        stmt = (
            update(Project)
            .where(
                Project.id == project_id,
                permission_subquery.exists(),
            )
            .values(**update_data)
            .returning(Project)
        )

        result = await self.db.execute(stmt)
        updated_project = result.scalar_one_or_none()

        if not updated_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project không tồn tại hoặc bạn không có quyền chỉnh sửa",
            )

        await self.db.commit()
        return ProjectBasicInfo.model_validate(updated_project)

    async def create_new_project(
        self, workspace_id: str, user_id: str, project_data: ProjectCreate
    ) -> ProjectResponse:
        """Logic tạo project mới trong workspace"""

        stmt_check = (
            select(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.role != WorkspaceRole.VIEWER,
                WorkspaceMember.deleted_at.is_(None),
            )
        )

        res = await self.db.execute(stmt_check)
        member = res.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace không tồn tại hoặc bạn không có quyền tạo project",
            )

        result = await self.db.execute(
            select(Project)
            .where(
                Project.workspace_id == workspace_id,
                Project.name == project_data.name
            )
        )
        existing_project = result.scalar_one_or_none()

        if existing_project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Đã có project này trong workspace",
            )

        new_project = Project(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            name=project_data.name,
            description=project_data.description,
            status=ProjectStatus.ACTIVE,
        )

        self.db.add(new_project)
        await self.db.commit()

        return ProjectResponse(
            id=new_project.id,
            workspace_id=new_project.workspace_id,
            name=new_project.name,
            description=new_project.description,
            status=new_project.status,
            tasks=TaskList(
                data=[],
                page=PageInfo(page_number=1, page_size=10, total_items=0),
            ),
        )

    async def get_project_basic_info(self, project_id: str) -> ProjectBasicInfo:
        """Logic lấy thông tin cơ bản của project"""

        res = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = res.scalar_one_or_none()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project không tồn tại",
            )
        return ProjectBasicInfo.model_validate(project)

    async def get_projects_in_workspace(
        self, workspace_id: uuid.UUID
    ) -> list[ProjectBasicInfo]:
        """Logic lấy danh sách project trong workspace"""

        res = await self.db.execute(
            select(Project).where(Project.workspace_id == workspace_id)
        )
        projects = res.scalars().all()

        return [ProjectBasicInfo.model_validate(p) for p in projects]

    async def check_permission(
        self, project_id: uuid.UUID, user_id: str,
        min_role: WorkspaceRole = WorkspaceRole.VIEWER
    ) -> None:
        """Logic kiểm tra quyền hạn của user trong project"""

        result = await self.db.execute(
            select(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == (
                    select(Project.workspace_id).where(Project.id == project_id)
                ),
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
