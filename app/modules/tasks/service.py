import uuid
from collections import defaultdict
from collections.abc import Sequence
from typing import cast

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.projects.models import Project
from app.modules.projects.schemas import (
    PageInfo,
    TaskList,
)
from app.modules.projects.service import ProjectService
from app.modules.tasks.models import Label, Task, TaskComment, TaskLabel, TaskStatus
from app.modules.tasks.schemas import (
    CommentRequest,
    CommentResponse,
    CreateTaskRequest,
    LabelResponse,
    TaskFilterRequest,
    TaskResponse,
    UpdateTaskRequest,
)
from app.modules.tasks.utils import apply_task_filters
from app.modules.workspaces.models import WorkspaceMember, WorkspaceRole
from app.services.redis import RedisClientWrapper


class TaskService:
    def __init__(
            self, db: AsyncSession,
            redis: RedisClientWrapper, project_service: ProjectService
        ):
        self.db = db
        self.redis = redis
        self.project_service = project_service

    async def _get_filtered_task_ids(
        self, project_id: uuid.UUID, filter: TaskFilterRequest
    ) -> list[uuid.UUID]:
        """Logic query db lấy danh sách ID theo filter"""
        stmt = (
            select(Task.id)
            .where(Task.project_id == project_id)
        )

        stmt = apply_task_filters(stmt, filter_req=filter)


        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def _get_tasks_from_db_by_ids(
        self, task_ids: list[uuid.UUID]
    ) -> Sequence[Task]:
        """Query DB lấy chi tiết các task bị miss cache"""
        if not task_ids:
            return []
        stmt = (
            select(Task)
            .where(Task.id.in_(task_ids))
            .options(
                selectinload(Task.assignee),
                selectinload(Task.creator),
                selectinload(Task.project)
            )
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def _get_tasks_from_cache(
        self, task_ids: list[uuid.UUID]
    ) -> tuple[dict[uuid.UUID, TaskResponse], list[uuid.UUID]]:
        """Lấy batch task từ Redis, trả về (cached_dict, missed_ids)"""
        if not task_ids:
            return {}, []

        cache_keys = [f"task:{tid}" for tid in task_ids]
        cached_bytes_list = await self.redis.safe_mget(cache_keys)

        cached_tasks: dict[uuid.UUID, TaskResponse] = {}
        missed_ids: list[uuid.UUID] = []

        for tid, cached_bytes in zip(task_ids, cached_bytes_list, strict=True):
            if cached_bytes:
                cached_tasks[tid] = TaskResponse.model_validate_json(cached_bytes)
            else:
                missed_ids.append(tid)

        return cached_tasks, missed_ids

    async def _set_tasks_to_cache(
        self, tasks: Sequence[Task], ttl_seconds: int = 86400
    ) -> list[TaskResponse]:
        """Ghi batch task vào Redis qua Pipeline & trả về DTO List"""
        if not tasks:
            return []

        task_dtos: list[TaskResponse] = []
        async with self.redis.safe_pipeline() as pipe:
            for task in tasks:
                dto = TaskResponse.model_validate(task)
                task_dtos.append(dto)
                pipe.set(f"task:{task.id}", dto.model_dump_json(), ex=ttl_seconds)

        return task_dtos

    async def _get_labels_for_task_ids(
        self, task_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[LabelResponse]]:
        if not task_ids:
            return {}

        # Query 1 lần lấy toàn bộ Label của tất cả task_id trong trang
        stmt = (
            select(Label, TaskLabel.task_id)
            .join(TaskLabel, Label.id == TaskLabel.label_id)
            .where(TaskLabel.task_id.in_(task_ids))
        )
        result = await self.db.execute(stmt)

        # Grouping data theo task_id dạng dict
        labels_map: dict[uuid.UUID, list[LabelResponse]] = defaultdict(list)
        for label, task_id in result.all():
            labels_map[task_id].append(LabelResponse.model_validate(label))

        return labels_map

    async def get_task_list_by_filter(
        self, project_id: uuid.UUID, filter_data: TaskFilterRequest
    ) -> TaskList:
        """Logic lấy thông tin danh sách Task theo filter"""

        # 1. Lấy toàn bộ Task IDs thỏa điều kiện
        all_ids = await self._get_filtered_task_ids(project_id, filter_data)
        total_items = len(all_ids)

        page = filter_data.page
        size = filter_data.size

        empty_task_list = TaskList(
            data=[],
            page=PageInfo(page_number=page, page_size=size, total_items=total_items),
        )

        if total_items == 0:
            return empty_task_list

        # 2. Slicing pagination trên RAM
        start = (page - 1) * size
        paged_ids = all_ids[start : start + size]

        if not paged_ids:
            return empty_task_list

        # 3. MGET từ Redis
        tasks_map, missed_ids = await self._get_tasks_from_cache(paged_ids)

        # 4. Fetch DB các ID bị miss & sync lại Cache
        if missed_ids:
            missed_db_tasks = await self._get_tasks_from_db_by_ids(missed_ids)
            missed_dtos = await self._set_tasks_to_cache(missed_db_tasks)
            # Cập nhật vào tasks_map hiện tại
            for dto in missed_dtos:
                tasks_map[dto.id] = dto

        # 5. Assemble đúng thứ tự paged_ids ban đầu
        ordered_tasks = [tasks_map[tid] for tid in paged_ids if tid in tasks_map]

        # 6. Fetch Labels (và Comment count/comments) theo Batch cho toàn bộ paged_ids
        labels_map = await self._get_labels_for_task_ids(paged_ids)
        # comment_counts_map = await self._get_comment_counts_for_task_ids(paged_ids)

        # 7. Enrich dữ liệu tươi vào từng Task DTO
        enriched_tasks = []
        for task in ordered_tasks:
            task_data = task.model_dump()
            task_data["labels"] = labels_map.get(task.id, [])
            # task_data["comment_count"] = comment_counts_map.get(task.id, 0)
            enriched_tasks.append(TaskResponse(**task_data))

        return TaskList(
            data=enriched_tasks,
            page=PageInfo(
                page_number=page,
                page_size=size,
                total_items=total_items,
            ),
        )

    async def create_new_task(
        self, project_id: uuid.UUID, creator: str, create_data: CreateTaskRequest
    ) -> TaskResponse:
        """Logic tạo Task mới"""

        await self.project_service.check_permission(
            project_id=project_id,
            user_id=creator,
            min_role=WorkspaceRole.EDITOR
        )

        if create_data.assignee_id:
            await self.project_service.check_permission(
                project_id=project_id,
                user_id=str(create_data.assignee_id),
                min_role=WorkspaceRole.VIEWER,
                is_check_assignee=True
            )

        result = await self.db.execute(
            select(Task.id)
            .where(
                Task.project_id == project_id,
                Task.title == create_data.title
            )
        )
        existing_task = result.scalar_one_or_none()

        if existing_task:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Đã có task này trong project",
            )

        new_task = Task(
            id=uuid.uuid4(),
            project_id=project_id,
            assignee_id=create_data.assignee_id,
            title=create_data.title,
            description=create_data.description,
            status=TaskStatus.TODO,
            priority=create_data.priority,
            due_date=create_data.due_date,
            created_by=uuid.UUID(creator)
        )

        self.db.add(new_task)
        await self.db.commit()
        await self.db.refresh(new_task, ["project", "assignee"])

        task_dto = TaskResponse.model_validate(new_task)

        try:
            await self.redis.safe_set(
                f"task:{new_task.id}",
                task_dto.model_dump_json(),
                ex=86400,
            )
        except Exception:
            pass

        return task_dto

    async def check_task_permission(
        self,
        task_id: uuid.UUID,
        user_id: str,
        min_role: WorkspaceRole = WorkspaceRole.EDITOR,
    ) -> Task:
        """Check quyền của user đối với 1 Task cụ thể.
        Trả về instance Task luôn để hàm update/delete bên dưới dùng tiếp
        """
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id

        stmt = (
            select(Task, WorkspaceMember.role)
            .join(Project, Task.project_id == Project.id)
            .join(
                WorkspaceMember,
                (WorkspaceMember.workspace_id == Project.workspace_id)
                & (WorkspaceMember.user_id == user_uuid)
                & (WorkspaceMember.deleted_at.is_(None)),
            )
            .where(Task.id == task_id)
        )

        result = await self.db.execute(stmt)
        row = result.first()

        not_found_or_forbidden = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền thực hiện thao tác này",
        )

        if not row:
            raise not_found_or_forbidden

        task, member_role = row

        if task.created_by == user_uuid or task.assignee_id == user_uuid:
            return cast(Task, task)

        if min_role == WorkspaceRole.EDITOR and member_role == WorkspaceRole.VIEWER:
            raise not_found_or_forbidden

        if min_role == WorkspaceRole.OWNER and member_role != WorkspaceRole.OWNER:
            raise not_found_or_forbidden

        return cast(Task, task)

    async def update_task(
        self, task_id: uuid.UUID, current_user_id: str, update_data: UpdateTaskRequest
    ) -> TaskResponse:
        task_info = await self.check_task_permission(
            task_id=task_id, user_id=current_user_id
        )

        if update_data.assignee_id:
            await self.project_service.check_permission(
                project_id=task_info.project_id,
                user_id=str(update_data.assignee_id),
                min_role=WorkspaceRole.VIEWER,
                is_check_assignee=True
            )

        update_dict = update_data.model_dump(exclude_unset=True)

        for key, value in update_dict.items():
            setattr(task_info, key, value)

        await self.db.commit()
        await self.db.refresh(task_info, ["project", "assignee"])

        task_dto = TaskResponse.model_validate(task_info)

        try:
            await self.redis.safe_set(
                f"task:{task_info.id}",
                task_dto.model_dump_json(),
                ex=86400,
            )
        except Exception:
            pass

        return task_dto

    async def delete_task(
        self, task_id: uuid.UUID, current_user_id: str
    ) -> None:
        task_info = await self.check_task_permission(
            task_id=task_id, user_id=current_user_id
        )

        await self.db.delete(task_info)
        await self.db.commit()

        try:
            await self.redis.safe_delete(f"task:{task_info.id}")
        except Exception:
            pass

        return None

    async def add_label(
        self, task_id: uuid.UUID, current_user_id: str, label_id: uuid.UUID
    ) -> None:
        await self.check_task_permission(
            task_id=task_id, user_id=current_user_id
        )

        stmt = (
            insert(TaskLabel)
            .values(task_id=task_id, label_id=label_id)
            .on_conflict_do_nothing()
        )

        try:
            await self.db.execute(stmt)
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Label không tồn tại"
            ) from None

        return None

    async def remove_label(
        self, task_id: uuid.UUID, current_user_id: str, label_id: uuid.UUID
    ) -> None:
        await self.check_task_permission(
            task_id=task_id, user_id=current_user_id
        )

        stmt = delete(TaskLabel).where(
            TaskLabel.task_id == task_id,
            TaskLabel.label_id == label_id,
        )

        await self.db.execute(stmt)
        await self.db.commit()

        return None

    async def add_comment(
        self, task_id: uuid.UUID, current_user_id: str, data: CommentRequest
    ) -> CommentResponse:
        """Logic tạo comment mới trong task"""

        await self.check_task_permission(
            task_id=task_id,
            user_id=current_user_id,
            min_role=WorkspaceRole.VIEWER
        )

        new_comment = TaskComment(
            id=uuid.uuid4(),
            task_id=task_id,
            author_id=current_user_id,
            content=data.content,
        )

        self.db.add(new_comment)
        await self.db.commit()
        await self.db.refresh(new_comment, ["author", "create_at"])

        return CommentResponse.model_validate(new_comment)


    async def edit_comment(
        self, task_id: uuid.UUID,
        current_user_id: str,
        comment_id: uuid.UUID,
        data: CommentRequest
    ) -> CommentResponse:
        """Logic sửa nội dung comment"""

        stmt = (
            select(TaskComment, Task.project_id)
            .join(Task, TaskComment.task_id == Task.id)
            .options(selectinload(TaskComment.author))
            .where(
                TaskComment.id == comment_id,
                TaskComment.task_id == task_id,
            )
        )

        result = await self.db.execute(stmt)
        row = result.first()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment không tồn tại hoặc dữ liệu không hợp lệ",
            )

        comment, project_id = row

        if comment.author_id != current_user_id:
            await self.project_service.check_permission(
                project_id=project_id,
                user_id=current_user_id,
                min_role=WorkspaceRole.OWNER
            )

        comment.content = data.content

        response = CommentResponse.model_validate(comment)

        await self.db.commit()

        return response

    async def delete_comment(
        self, task_id: uuid.UUID,
        current_user_id: str,
        comment_id: uuid.UUID,
    ) -> None:
        """Logic xóa comment"""

        stmt = (
            select(TaskComment, Task.project_id)
            .join(Task, TaskComment.task_id == Task.id)
            .where(
                TaskComment.id == comment_id,
                TaskComment.task_id == task_id,
            )
        )

        result = await self.db.execute(stmt)
        row = result.first()

        if not row:
            return None

        comment, project_id = row

        if comment.author_id != current_user_id:
            await self.project_service.check_permission(
                project_id=project_id,
                user_id=current_user_id,
                min_role=WorkspaceRole.OWNER
            )

        await self.db.execute(
            delete(TaskComment).where(TaskComment.id == comment.id)
        )
        await self.db.commit()

        return None
