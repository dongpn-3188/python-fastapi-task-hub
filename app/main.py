from fastapi import FastAPI, Path, Query
from enum import Enum

app = FastAPI(
    title="TaskHub API",
    description="API cho ứng dụng quản lý công việc TaskHub",
    version="1.0.0",
)

MOCK_TASKS = [
    {"id": 1, "title": "Hoàn thành báo cáo", "description": "Hoàn thành báo cáo tài chính cho quý 2", "status": "pending"},
    {"id": 2, "title": "Gửi email cho khách hàng", "description": "Gửi email thông báo về chương trình khuyến mãi", "status": "completed"},
    {"id": 3, "title": "Lập kế hoạch dự án", "description": "Lập kế hoạch chi tiết cho dự án mới", "status": "in_progress"},
]

@app.get("/")
def read_root():
    return {"message": "Chào mừng bạn đến với TaskHub API!"}

@app.get("/health", tags=["System"])
async def read_health():
    return {
        "status": "Healthy",
        "message": "Hệ thống đang hoạt động bình thường",
        "version": "1.0.0"
    }

class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"

@app.get("/tasks", tags=["Tasks"])
async def search_tasks(
    keyword: str | None = None,
    limit: int = 10,
):
    tasks = MOCK_TASKS
    if keyword:
        tasks = [task for task in tasks if keyword.lower() in task["title"].lower() or keyword.lower() in task["description"].lower()]
    return tasks[:limit]

@app.get("/tasks/status/{status}", tags=["Tasks"])
async def read_tasks_by_status(status: TaskStatus):
    tasks = [task for task in MOCK_TASKS if task["status"] == status.value]
    return tasks

@app.get("/tasks/{task_id}", tags=["Tasks"])
async def read_task(task_id: int):
    task = next((task for task in MOCK_TASKS if task["id"] == task_id), None)
    if task:
        return task
    return {"error": "Task not found"}

@app.get("/tasks/secure/{task_id}", tags=["Tasks"])
async def read_task_secure(
    task_id: int = Path(..., ge=1, le=10000),
    keyword: str | None = Query(
        default = None, 
        min_length=3, max_length=50,
        pattern="^[a-zA-Z0-9_ ]*$"
    )
):
    return {"status":"data validation"}