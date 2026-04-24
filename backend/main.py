"""
TaleVoice应用主入口

FastAPI应用配置，包括：
- 中间件配置（CORS、日志）
- 路由注册
- 生命周期事件处理
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.api import user_router, voice_sample_router, project_router, common_router, video_router, bgm_router
from app.core.config import settings
from app.core.logger import app_logger
from app.core.middleware import RequestLoggingMiddleware
from app.core.database import engine, Base
from app.schemas.common import ResponseModel, APIException

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用的生命周期管理 (替代 on_event)
    """
    # ====== 启动阶段 (Startup) ======
    app_logger.info(f"{settings.APP_NAME} 服务启动")
    # 创建数据库表结构
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # ⬅️ 关键：应用在此处挂起并开始处理接收到的请求

    # ====== 关闭阶段 (Shutdown) ======
    app_logger.info(f"{settings.APP_NAME} 服务关闭")
    # 关闭数据库连接
    await engine.dispose()

    
app = FastAPI(
    title=settings.APP_NAME,
    description="TaleVoice - AI故事语音生成平台",
    version="1.0.0",
    lifespan=lifespan
)


@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """自定义API异常处理器"""
    app_logger.warning(f"API异常: {exc.code} - {exc.message}")
    return JSONResponse(
        status_code=200,
        content=ResponseModel(code=exc.code, message=exc.message, data=exc.data).model_dump()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTPException异常处理器，转换为统一响应格式"""
    app_logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")
    message = exc.detail if isinstance(exc.detail, str) else "操作失败"
    return JSONResponse(
        status_code=200,
        content=ResponseModel(code=exc.status_code, message=message, data=None).model_dump()
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)

app.include_router(user_router)
app.include_router(voice_sample_router)
app.include_router(project_router)
app.include_router(common_router)
app.include_router(video_router)
app.include_router(bgm_router)


@app.get("/")
async def root():
    """API根路径，返回欢迎信息"""
    return {"message": "Welcome to TaleVoice API"}


@app.get("/health")
async def health_check():
    """健康检查接口，用于监控服务状态"""
    return {"status": "healthy"}
