"""
阿里云通义万相视频生成服务适配器

通过阿里云DashScope API实现图生视频功能
支持模型: wanx2.1-i2v-plus, wanx2.1-i2v-turbo
API文档: https://help.aliyun.com/zh/model-studio/image-to-video-general-api-reference
"""

import hashlib
import hmac
import base64
import datetime
import json
import uuid
from typing import Optional
from urllib.parse import quote

from app.core.config import settings
from app.core.logger import app_logger
from app.services.ai_provider import AIProvider, VideoGenerationResult


class AliyunProvider(AIProvider):
    """
    阿里云通义万相视频生成服务商

    通过阿里云DashScope API实现图片+文本生成视频
    支持首帧生视频、首尾帧生视频、视频续写三大任务
    """

    def __init__(self):
        """初始化阿里云服务商，从配置读取API密钥和地址"""
        self.access_key_id = getattr(settings, "ALIYUN_ACCESS_KEY_ID", "")
        self.access_key_secret = getattr(settings, "ALIYUN_ACCESS_KEY_SECRET", "")
        self.api_key = getattr(settings, "ALIYUN_VIDEO_API_KEY", "")
        self.endpoint = getattr(
            settings,
            "ALIYUN_VIDEO_ENDPOINT",
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation"
        )
        self.model = getattr(settings, "ALIYUN_VIDEO_MODEL", "wanx2.1-i2v-plus")
        self._timeout = 300

    def _generate_signature(self, string_to_sign: str) -> str:
        """
        生成API签名

        Args:
            string_to_sign: 待签名字符串

        Returns:
            str: Base64编码的签名
        """
        h = hmac.new(
            self.access_key_secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha1
        )
        signature = base64.b64encode(h.digest()).decode('utf-8')
        return signature

    def _build_headers(self, content_type: str = "application/json") -> dict:
        """
        构建API请求头

        Args:
            content_type: 内容类型

        Returns:
            dict: 请求头字典
        """
        timestamp = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

        headers = {
            "Content-Type": content_type,
            "Authorization": f"Bearer {self.api_key}",
            "X-DashScope-Async": "enable",
            "Date": timestamp
        }

        return headers

    async def generate_video(
        self,
        image_url: str,
        prompt: str,
        duration: Optional[int] = None,
        resolution: Optional[str] = None,
        fps: Optional[int] = None
    ) -> VideoGenerationResult:
        """
        通过阿里云API提交视频生成任务（首帧生视频）

        Args:
            image_url: 源图片URL
            prompt: 生成提示词
            duration: 目标时长(秒)，阿里云默认4秒，最长12秒
            resolution: 目标分辨率 (720p/1080p)
            fps: 目标帧率

        Returns:
            VideoGenerationResult: 包含阿里云任务ID的结果
        """
        try:
            import httpx

            headers = self._build_headers()

            resolution_map = {
                "1280x720": "720P",
                "1920x1080": "720P",
                "720p": "720P",
                "720P": "720P",
                "480p": "480P",
                "480P": "480P",
                "1080p": "720P",
                "1080P": "720P"
            }
            mapped_resolution = resolution_map.get(resolution, "720P")

            payload = {
                "model": self.model,
                "input": {
                    "img_url": image_url,
                    "prompt": prompt
                },
                "parameters": {
                    "video_duration": str(min(duration or 4, 12)),
                    "resolution": mapped_resolution
                }
            }

            api_url = f"{self.endpoint}/video-synthesis"

            app_logger.info(f"[AliyunProvider] 提交视频生成请求: {api_url}")
            app_logger.debug(f"[AliyunProvider] 请求参数: {payload}")

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    api_url,
                    headers=headers,
                    json=payload
                )

                if response.status_code != 200:
                    error_text = response.text
                    app_logger.error(f"[AliyunProvider] API响应错误: {response.status_code} - {error_text}")
                    return VideoGenerationResult(
                        status="failed",
                        error_message=f"API请求失败: {response.status_code} - {error_text}"
                    )

                data = response.json()

            app_logger.info(f"[AliyunProvider] API响应: {data}")

            output = data.get("output", {})
            task_id = output.get("task_id", "") or data.get("request_id", "") or output.get("task_id")

            if not task_id:
                app_logger.error(f"[AliyunProvider] 未获取到任务ID: {data}")
                return VideoGenerationResult(
                    status="failed",
                    error_message="API未返回任务ID"
                )

            app_logger.info(f"[AliyunProvider] 视频生成任务已提交: {task_id}")

            return VideoGenerationResult(
                task_id=task_id,
                status="processing"
            )

        except ImportError:
            app_logger.error("[AliyunProvider] httpx未安装，请执行 pip install httpx")
            return VideoGenerationResult(
                status="failed",
                error_message="httpx未安装"
            )
        except httpx.HTTPStatusError as e:
            error_body = ""
            try:
                error_body = e.response.text
            except:
                pass
            app_logger.error(f"[AliyunProvider] API请求失败: {e.response.status_code} - {error_body}")
            return VideoGenerationResult(
                status="failed",
                error_message=f"API请求失败: {e.response.status_code}"
            )
        except Exception as e:
            app_logger.error(f"[AliyunProvider] 视频生成失败: {str(e)}")
            return VideoGenerationResult(
                status="failed",
                error_message=str(e)
            )

    async def generate_video_with_end_frame(
        self,
        start_image_url: str,
        end_image_url: str,
        prompt: str,
        duration: Optional[int] = None,
        resolution: Optional[str] = None
    ) -> VideoGenerationResult:
        """
        首尾帧生视频 - 通过首尾帧图片生成过渡视频

        Args:
            start_image_url: 首帧图片URL
            end_image_url: 尾帧图片URL
            prompt: 生成提示词
            duration: 目标时长(秒)
            resolution: 目标分辨率

        Returns:
            VideoGenerationResult: 生成结果
        """
        try:
            import httpx

            headers = self._build_headers()

            resolution_map = {
                "1280x720": "720p",
                "1920x1080": "1080p",
                "720p": "720p",
                "1080p": "1080p"
            }
            mapped_resolution = resolution_map.get(resolution, "720p")

            payload = {
                "model": self.model,
                "input": {
                    "first_frame_image_url": start_image_url,
                    "last_frame_image_url": end_image_url,
                    "prompt": prompt
                },
                "parameters": {
                    "duration": min(duration or 4, 12),
                    "resolution": mapped_resolution
                }
            }

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    self.endpoint,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

            output = data.get("output", {})
            task_id = output.get("task_id", "") or data.get("request_id", "")

            app_logger.info(f"[AliyunProvider] 首尾帧视频生成任务已提交: {task_id}")

            return VideoGenerationResult(
                task_id=task_id,
                status="processing"
            )

        except Exception as e:
            app_logger.error(f"[AliyunProvider] 首尾帧视频生成失败: {str(e)}")
            return VideoGenerationResult(
                status="failed",
                error_message=str(e)
            )

    async def extend_video(
        self,
        video_url: str,
        prompt: str,
        extend_duration: Optional[int] = None
    ) -> VideoGenerationResult:
        """
        视频续写 - 基于已有视频继续生成后续内容

        Args:
            video_url: 原视频URL
            prompt: 续写提示词
            extend_duration: 续写时长(秒)

        Returns:
            VideoGenerationResult: 生成结果
        """
        try:
            import httpx

            headers = self._build_headers()

            payload = {
                "model": self.model,
                "input": {
                    "video_url": video_url,
                    "prompt": prompt
                },
                "parameters": {
                    "extend_duration": min(extend_duration or 4, 12)
                }
            }

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    self.endpoint,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

            output = data.get("output", {})
            task_id = output.get("task_id", "") or data.get("request_id", "")

            app_logger.info(f"[AliyunProvider] 视频续写任务已提交: {task_id}")

            return VideoGenerationResult(
                task_id=task_id,
                status="processing"
            )

        except Exception as e:
            app_logger.error(f"[AliyunProvider] 视频续写失败: {str(e)}")
            return VideoGenerationResult(
                status="failed",
                error_message=str(e)
            )

    async def get_task_status(self, task_id: str) -> VideoGenerationResult:
        """
        查询阿里云任务生成状态

        Args:
            task_id: 阿里云任务ID

        Returns:
            VideoGenerationResult: 当前生成状态和结果
        """
        try:
            import httpx

            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }

            query_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"

            app_logger.info(f"[AliyunProvider] 查询任务状态: {query_url}")

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    query_url,
                    headers=headers
                )

                if response.status_code != 200:
                    error_text = response.text
                    app_logger.error(f"[AliyunProvider] 查询任务状态失败: {response.status_code} - {error_text}")
                    return VideoGenerationResult(
                        task_id=task_id,
                        status="failed",
                        error_message=f"查询失败: {response.status_code}"
                    )

                data = response.json()

            app_logger.info(f"[AliyunProvider] 查询响应: {data}")

            output = data.get("output", {})
            task_status = output.get("task_status", "PENDING")

            status_map = {
                "PENDING": "pending",
                "RUNNING": "processing",
                "SUCCEEDED": "completed",
                "FAILED": "failed",
                "CANCELED": "failed",
                "UNKNOWN": "failed"
            }

            mapped_status = status_map.get(task_status, "pending")

            result = VideoGenerationResult(
                task_id=task_id,
                status=mapped_status
            )

            if mapped_status == "completed":
                video_url = output.get("video_url", "")
                result.video_url = video_url
                result.duration = output.get("duration")
                result.resolution = output.get("resolution")
                result.fps = output.get("fps")
                result.format = "mp4"

                if video_url:
                    result.thumbnail_url = video_url.replace(".mp4", "_thumbnail.jpg")

            if mapped_status == "failed":
                result.error_message = output.get("message", "生成失败")
                app_logger.error(f"[AliyunProvider] 任务失败: {result.error_message}")

            if mapped_status == "processing":
                progress = output.get("progress", 0)
                app_logger.info(f"[AliyunProvider] 任务进度: {progress}%")

            return result

        except Exception as e:
            app_logger.error(f"[AliyunProvider] 查询任务状态失败: {str(e)}")
            return VideoGenerationResult(
                task_id=task_id,
                status="failed",
                error_message=str(e)
            )

    async def cancel_task(self, task_id: str) -> bool:
        """
        取消正在进行的视频生成任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否取消成功
        """
        try:
            import httpx

            headers = self._build_headers()

            cancel_url = f"{self.endpoint}/tasks/{task_id}/cancel"

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    cancel_url,
                    headers=headers
                )
                response.raise_for_status()

            app_logger.info(f"[AliyunProvider] 任务已取消: {task_id}")
            return True

        except Exception as e:
            app_logger.error(f"[AliyunProvider] 取消任务失败: {str(e)}")
            return False


aliyun_provider = AliyunProvider()
