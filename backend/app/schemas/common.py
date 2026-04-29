"""
通用数据Schema

定义通用上传接口的请求和响应数据结构
"""

from typing import Optional, Any

from pydantic import BaseModel


class ResponseModel(BaseModel):
    """通用响应Schema"""
    code: int
    message: str
    data: Optional[Any] = None


class UploadResponse(BaseModel):
    """文件上传响应Schema"""
    code: int
    msg: str
    data: Optional[str] = None


class ErrorCode:
    """错误码常量定义"""
    SUCCESS = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500


class APIException(Exception):
    """自定义API异常类"""
    def __init__(
        self,
        code: int = ErrorCode.BAD_REQUEST,
        message: str = "操作失败",
        data: Optional[Any] = None
    ):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


def success_response(message: str = "操作成功", data: Optional[Any] = None) -> ResponseModel:
    """成功响应"""
    return ResponseModel(code=200, message=message, data=data)


def error_response(message: str = "操作失败", code: int = 400, data: Optional[Any] = None) -> ResponseModel:
    """错误响应"""
    return ResponseModel(code=code, message=message, data=data)
