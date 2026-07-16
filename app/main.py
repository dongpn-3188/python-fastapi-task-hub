from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router

app = FastAPI(
    title="TaskHub API",
    description="API cho ứng dụng quản lý công việc TaskHub",
    version="1.0.0",
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")

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

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()

    error_msg = errors[0].get("msg", "Dữ liệu đầu vào không hợp lệ")

    if error_msg.startswith("Value error, "):
        error_msg = error_msg.replace("Value error, ", "")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": error_msg
        },
    )
