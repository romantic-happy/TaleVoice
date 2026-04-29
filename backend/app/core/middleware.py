"""
请求日志中间件

记录每个HTTP请求的完整生命周期，包括：
- 请求开始时的方法、URL、客户端IP
- 请求完成时的状态码、处理耗时
- 请求异常时的错误信息
"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logger import app_logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    HTTP请求日志中间件

    继承自BaseHTTPMiddleware，在每个请求前后记录日志
    并在响应头中添加X-Process-Time表示处理耗时
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求的主方法

        记录请求开始、计算处理时间、记录请求完成或异常信息

        Args:
            request: FastAPI请求对象
            call_next: 下一个处理函数（执行业务逻辑）

        Returns:
            Response: HTTP响应对象

        Raises:
            Exception: 业务逻辑执行时发生的异常
        """
        start_time = time.time()

        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        url = str(request.url)

        app_logger.info(f"请求开始: {method} {url} - 客户端: {client_ip}")

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            app_logger.info(
                f"请求完成: {method} {url} - "
                f"状态码: {response.status_code} - "
                f"耗时: {process_time:.3f}s"
            )

            response.headers["X-Process-Time"] = str(process_time)
            return response

        except Exception as e:
            process_time = time.time() - start_time
            app_logger.error(
                f"请求异常: {method} {url} - "
                f"错误: {str(e)} - "
                f"耗时: {process_time:.3f}s",
                exc_info=True
            )
            raise
