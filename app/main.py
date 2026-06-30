from typing import Any

from fastapi import FastAPI

app = FastAPI(
    title="TaskHub API",
    description="API cho ứng dụng quản lý công việc TaskHub",
    version="1.0.0",
)


@app.get("/")
def read_root() -> dict[str, Any]:
    return {"message": "Chào mừng bạn đến với TaskHub API!"}


@app.get("/health", tags=["System"])
async def read_health() -> dict[str, Any]:
    return {
        "status": "Healthy",
        "message": "Hệ thống đang hoạt động bình thường",
        "version": "1.0.0",
    }
