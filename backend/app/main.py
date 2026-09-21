import time
import uuid
import os

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import AppException
from app.database import init_db

setup_logging()
logger = structlog.get_logger()

app = FastAPI(
    title="Seedance Studio API",
    description="AI视频创作平台API",
    version="1.0.0",
)

# CORS - 开发阶段允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_headers(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.correlation_id = request_id
    start_time = time.time()

    logger.info("request_received", method=request.method, path=request.url.path)

    response = await call_next(request)

    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.3f}s"

    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time=f"{process_time:.3f}s",
    )

    return response


# Exception handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试"},
    )


# Startup event
@app.on_event("startup")
async def startup():
    logger.info("正在初始化数据库...")
    os.makedirs(settings.storage_path, exist_ok=True)
    os.makedirs(settings.upload_path, exist_ok=True)
    os.makedirs(settings.video_path, exist_ok=True)
    os.makedirs(settings.image_path, exist_ok=True)
    os.makedirs(settings.temp_path, exist_ok=True)
    await init_db()
    logger.info("数据库初始化完成")


# 导入API路由（必须在catch-all之前注册）
from app.api.v1 import api_router

app.include_router(api_router, prefix="/api/v1")

# SPA前端 - 所有非API路径返回index.html
FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"
index_html = FRONTEND_DIR / "index.html"

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")

    @app.get("/")
    async def serve_root():
        return FileResponse(str(index_html))

    @app.api_route("/{full_path:path}", methods=["GET"])
    async def serve_spa(full_path: str):
        if full_path.startswith(("api/", "storage/", "ws/")):
            return JSONResponse({"detail": "Not found"}, status_code=404)
        return FileResponse(str(index_html))

# 存储静态文件
if os.path.exists(settings.storage_path):
    app.mount("/storage", StaticFiles(directory=settings.storage_path), name="storage")
