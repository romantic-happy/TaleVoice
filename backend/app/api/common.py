"""
通用模块API路由

提供文件上传等通用接口
"""

from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import JSONResponse

from app.core.security import get_current_user_optional
from app.core.logger import app_logger
from app.core.oss import oss_client
from app.schemas.common import UploadResponse, ResponseModel, APIException, ErrorCode

router = APIRouter(prefix="/common", tags=["通用模块"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp3", ".wav", ".ogg"}
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user_optional)
):
    """
    文件上传接口

    - 可选JWT认证
    - 支持图片和音频文件上传
    - 使用阿里云OSS存储，返回OSS文件URL
    """
    client_name = current_user.get("username") if current_user else "anonymous"
    app_logger.info(f"文件上传请求: {client_name}, 文件名: {file.filename}")

    if not file.filename:
        app_logger.warning(f"文件上传失败-文件名为空")
        raise APIException(code=ErrorCode.BAD_REQUEST, message="文件名为空")

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        app_logger.warning(f"文件上传失败-不支持的文件类型: {file_ext}")
        raise APIException(code=ErrorCode.BAD_REQUEST, message=f"不支持的文件类型，仅支持: {', '.join(ALLOWED_EXTENSIONS)}")

    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        app_logger.warning(f"文件上传失败-文件过大: {len(file_content)} bytes")
        raise APIException(code=ErrorCode.BAD_REQUEST, message=f"文件大小超过限制，最大{MAX_FILE_SIZE // (1024 * 1024)}MB")

    try:
        file_url = oss_client.upload_file(file_content, file_ext)
        app_logger.info(f"文件上传成功: {file_url}")
        return UploadResponse(code=1, msg="上传成功", data=file_url)
    except Exception as e:
        app_logger.error(f"文件上传到OSS失败: {str(e)}")
        raise APIException(code=ErrorCode.INTERNAL_SERVER_ERROR, message="文件上传失败，请稍后重试")
