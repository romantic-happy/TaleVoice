from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
from app.core.config import settings


@dataclass
class VideoGenerationResult:
    task_id: Optional[str] = None
    status: str = "pending"
    video_url: Optional[str] = None
    error_message: Optional[str] = None


class AIProvider(ABC):
    @abstractmethod
    async def generate_video(
        self,
        image_url: str,
        prompt: str,
        duration: Optional[int] = None,
        resolution: Optional[str] = None,
        fps: Optional[int] = None
    ) -> VideoGenerationResult:
        pass

    @abstractmethod
    async def get_task_status(self, task_id: str) -> VideoGenerationResult:
        pass


class MockProvider(AIProvider):
    async def generate_video(
        self,
        image_url: str,
        prompt: str,
        duration: Optional[int] = None,
        resolution: Optional[str] = None,
        fps: Optional[int] = None
    ) -> VideoGenerationResult:
        return VideoGenerationResult(
            task_id="mock-task-id",
            status="processing"
        )

    async def get_task_status(self, task_id: str) -> VideoGenerationResult:
        return VideoGenerationResult(
            task_id=task_id,
            status="completed",
            video_url="https://example.com/mock_video.mp4"
        )


class AliyunProvider(AIProvider):
    def __init__(self):
        self.api_key = settings.ALIYUN_VIDEO_API_KEY
        self.endpoint = settings.ALIYUN_VIDEO_ENDPOINT
        self.model = settings.ALIYUN_VIDEO_MODEL

    async def generate_video(
        self,
        image_url: str,
        prompt: str,
        duration: Optional[int] = None,
        resolution: Optional[str] = None,
        fps: Optional[int] = None
    ) -> VideoGenerationResult:
        try:
            import httpx

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

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

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    api_url,
                    headers=headers,
                    json=payload
                )

                if response.status_code != 200:
                    error_text = response.text
                    return VideoGenerationResult(
                        status="failed",
                        error_message=f"API请求失败: {response.status_code} - {error_text}"
                    )

                data = response.json()

            output = data.get("output", {})
            task_id = output.get("task_id", "") or data.get("request_id", "")

            return VideoGenerationResult(
                task_id=task_id,
                status="processing"
            )
        except Exception as e:
            return VideoGenerationResult(
                status="failed",
                error_message=str(e)
            )

    async def get_task_status(self, task_id: str) -> VideoGenerationResult:
        try:
            import httpx

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            api_url = f"{self.endpoint}/video-synthesis/{task_id}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(api_url, headers=headers)

                if response.status_code != 200:
                    return VideoGenerationResult(
                        task_id=task_id,
                        status="failed",
                        error_message=f"查询失败: {response.status_code}"
                    )

                data = response.json()

            output = data.get("output", {})
            status = output.get("task_status", "unknown")
            
            status_map = {
                "PENDING": "pending",
                "RUNNING": "processing",
                "SUCCEEDED": "completed",
                "FAILED": "failed"
            }
            mapped_status = status_map.get(status, status.lower())

            video_url = output.get("video_url") if mapped_status == "completed" else None
            error_message = output.get("message") if mapped_status == "failed" else None

            return VideoGenerationResult(
                task_id=task_id,
                status=mapped_status,
                video_url=video_url,
                error_message=error_message
            )
        except Exception as e:
            return VideoGenerationResult(
                task_id=task_id,
                status="failed",
                error_message=str(e)
            )


def get_ai_provider() -> AIProvider:
    provider = settings.AI_PROVIDER.lower()
    if provider == "aliyun":
        return AliyunProvider()
    return MockProvider()


ai_provider = get_ai_provider()
