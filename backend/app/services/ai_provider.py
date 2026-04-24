"""
AI视频生成服务适配器层

提供统一的AI视频生成接口，支持AI服务商的切换
当前支持: Mock(测试用), 阿里云通义万相
采用策略模式，通过配置切换不同的AI服务商
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass

from app.core.config import settings
from app.core.logger import app_logger


@dataclass
class VideoGenerationResult:
    """
    AI视频生成结果数据类

    Attributes:
        task_id: AI服务商返回的任务ID
        video_url: 生成视频的文件URL
        duration: 视频时长(秒)
        resolution: 视频分辨率
        fps: 帧率
        file_size: 文件大小(字节)
        format: 视频格式
        thumbnail_url: 缩略图URL
        status: 生成状态(pending/processing/completed/failed)
        error_message: 错误信息
    """
    task_id: str = ""
    video_url: Optional[str] = None
    duration: Optional[int] = None
    resolution: Optional[str] = None
    fps: Optional[int] = None
    file_size: Optional[int] = None
    format: str = "mp4"
    thumbnail_url: Optional[str] = None
    status: str = "pending"
    error_message: Optional[str] = None


class AIProvider(ABC):
    """
    AI视频生成服务商抽象基类

    定义统一的AI视频生成接口，所有服务商实现必须继承此类
    """

    @abstractmethod
    async def generate_video(
        self,
        image_url: str,
        prompt: str,
        duration: Optional[int] = None,
        resolution: Optional[str] = None,
        fps: Optional[int] = None
    ) -> VideoGenerationResult:
        """
        提交视频生成任务

        Args:
            image_url: 源图片URL
            prompt: 生成提示词
            duration: 目标时长(秒)，None使用默认值
            resolution: 目标分辨率，None使用默认值
            fps: 目标帧率，None使用默认值

        Returns:
            VideoGenerationResult: 生成结果，包含任务ID和状态
        """
        pass

    @abstractmethod
    async def get_task_status(self, task_id: str) -> VideoGenerationResult:
        """
        查询任务生成状态

        Args:
            task_id: AI服务商返回的任务ID

        Returns:
            VideoGenerationResult: 当前生成状态和结果
        """
        pass


class MockProvider(AIProvider):
    """
    Mock AI服务商

    用于开发和测试环境，模拟AI视频生成过程
    生成延迟可配置，默认5秒完成
    """

    def __init__(self, delay_seconds: int = 5):
        """
        初始化Mock服务商

        Args:
            delay_seconds: 模拟生成延迟时间(秒)
        """
        self.delay_seconds = delay_seconds
        self._tasks: dict = {}

    async def generate_video(
        self,
        image_url: str,
        prompt: str,
        duration: Optional[int] = None,
        resolution: Optional[str] = None,
        fps: Optional[int] = None
    ) -> VideoGenerationResult:
        """
        模拟提交视频生成任务

        创建一个模拟任务，延迟后自动标记为完成

        Args:
            image_url: 源图片URL
            prompt: 生成提示词
            duration: 目标时长(秒)
            resolution: 目标分辨率
            fps: 目标帧率

        Returns:
            VideoGenerationResult: 包含模拟任务ID的结果
        """
        task_id = str(uuid.uuid4())
        app_logger.info(f"[MockProvider] 创建模拟视频生成任务: {task_id}")

        self._tasks[task_id] = {
            "image_url": image_url,
            "prompt": prompt,
            "duration": duration or 10,
            "resolution": resolution or "1280x720",
            "fps": fps or 24,
            "status": "processing",
            "created_at": asyncio.get_event_loop().time()
        }

        asyncio.create_task(self._simulate_processing(task_id))

        return VideoGenerationResult(
            task_id=task_id,
            status="processing"
        )

    async def _simulate_processing(self, task_id: str):
        """
        模拟异步处理过程

        延迟后将任务状态更新为完成

        Args:
            task_id: 模拟任务ID
        """
        await asyncio.sleep(self.delay_seconds)

        if task_id in self._tasks:
            self._tasks[task_id]["status"] = "completed"
            app_logger.info(f"[MockProvider] 模拟视频生成完成: {task_id}")

    async def get_task_status(self, task_id: str) -> VideoGenerationResult:
        """
        查询模拟任务状态

        Args:
            task_id: 模拟任务ID

        Returns:
            VideoGenerationResult: 当前任务状态
        """
        if task_id not in self._tasks:
            return VideoGenerationResult(
                task_id=task_id,
                status="failed",
                error_message="任务不存在"
            )

        task = self._tasks[task_id]
        result = VideoGenerationResult(
            task_id=task_id,
            status=task["status"],
            duration=task["duration"],
            resolution=task["resolution"],
            fps=task["fps"],
            format="mp4"
        )

        if task["status"] == "completed":
            result.video_url = f"https://cdn.example.com/mock/videos/{task_id}.mp4"
            result.thumbnail_url = f"https://cdn.example.com/mock/thumbnails/{task_id}.jpg"
            result.file_size = task["duration"] * task["fps"] * 1024

        return result


def get_ai_provider() -> AIProvider:
    """
    获取当前配置的AI视频生成服务商

    根据settings.AI_PROVIDER配置返回对应的AI服务商实例
    支持的值: mock, aliyun

    Returns:
        AIProvider: AI视频生成服务商实例
    """
    provider_name = getattr(settings, "AI_PROVIDER", "mock").lower()

    if provider_name == "aliyun":
        try:
            from app.services.aliyun_provider import AliyunProvider
            app_logger.info("AI视频生成服务商: aliyun")
            return AliyunProvider()
        except ImportError as e:
            app_logger.error(f"[get_ai_provider] 无法导入阿里云适配器: {str(e)}，使用Mock服务商")
            return MockProvider()

    app_logger.info("AI视频生成服务商: mock")
    return MockProvider()


ai_provider = get_ai_provider()
