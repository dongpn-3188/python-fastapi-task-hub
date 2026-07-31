import uuid
from typing import Any
from sqlalchemy import ColumnElement, select
from sqlalchemy.orm import InstrumentedAttribute

from app.modules.tasks.models import Task
from app.modules.tasks.schemas import FilterField, FilterMethod, TaskFilterRequest

# Map FilterField sang Column tương ứng trong Model SQLAlchemy
FIELD_MAP: dict[FilterField, InstrumentedAttribute[Any]] = {
    FilterField.ASSIGNEE: Task.assignee_id,
    FilterField.TITLE: Task.title,
    FilterField.DESCRIPTION: Task.description,
    FilterField.STATUS: Task.status,
    FilterField.PRIORITY: Task.priority,
    FilterField.DUE_DATE: Task.due_date,
    FilterField.CREATE_BY: Task.created_by,
    FilterField.CREATE_AT: Task.created_at,
}


def apply_task_filters(stmt, filter_req: TaskFilterRequest):
    """Convert filter request thành sql condition"""
    if not filter_req or not filter_req.filter:
        return stmt

    conditions: list[ColumnElement[bool]] = []

    for item in filter_req.filter:
        column = FIELD_MAP.get(item.field)
        if column is None:
            continue

        val: Any = item.value
        if item.field in (FilterField.ASSIGNEE, FilterField.CREATE_BY):
            try:
                val = uuid.UUID(item.value)
            except (ValueError, TypeError):
                continue
        
        match item.method:
            case FilterMethod.IS:
                conditions.append(column == val)

            case FilterMethod.IS_NOT:
                conditions.append(column != val)

            case FilterMethod.CONTAIN:
                safe_val = (
                    str(val)
                    .replace("\\", r"\\")
                    .replace("%", r"\%")
                    .replace("_", r"\_")
                )
                conditions.append(column.ilike(f"%{safe_val}%"))

            case FilterMethod.DOESNT_CONTAIN:
                safe_val = (
                    str(val)
                    .replace("\\", r"\\")
                    .replace("%", r"\%")
                    .replace("_", r"\_")
                )
                conditions.append(~column.ilike(f"%{safe_val}%"))

            case FilterMethod.GREATER:
                conditions.append(column > val)

            case FilterMethod.LESS:
                conditions.append(column < val)

    if conditions:
        stmt = stmt.where(*conditions)

    return stmt