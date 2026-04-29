from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any
from app.models.video import Video
from app.services.ai_provider import get_ai_provider
from app.services.prompt_engine import prompt_engine
import uuid
from datetime import datetime


class VideoService:
    def __init__(self):
        self.ai_provider = get_ai_provider()

    async def create_video_task(
        self,
        db: AsyncSession,
        user_id: str,
        project_id: str,
        image_content: bytes,
        prompt: str,
        duration: int = 4,
        resolution: str = "720p"
    ) -> Dict[str, Any]:
        image_url = await self._upload_image(image_content)
        
        result = await self.ai_provider.generate_video(
            image_url=image_url,
            prompt=prompt,
            duration=duration,
            resolution=resolution
        )
        
        video = Video(
            video_id=str(uuid.uuid4()),
            project_id=project_id,
            user_id=user_id,
            source_image_url=image_url,
            prompt=prompt,
            duration=duration,
            resolution=resolution,
            status=result.status,
            task_id=result.task_id,
            create_time=datetime.utcnow(),
            update_time=datetime.utcnow()
        )
        
        db.add(video)
        await db.commit()
        await db.refresh(video)
        
        return {
            "video_id": video.video_id,
            "task_id": result.task_id,
            "status": result.status
        }

    async def get_task_status(self, db: AsyncSession, task_id: str) -> Dict[str, Any]:
        result = await self.ai_provider.get_task_status(task_id)
        
        stmt = select(Video).where(Video.task_id == task_id)
        video_result = await db.execute(stmt)
        video = video_result.scalar_one_or_none()
        
        if video and result.status == "completed":
            video.status = "completed"
            video.file_url = result.video_url
            video.update_time = datetime.utcnow()
            await db.commit()
        
        return {
            "task_id": task_id,
            "status": result.status,
            "video_url": result.video_url if result.status == "completed" else None,
            "error_message": result.error_message
        }

    async def list_project_videos(self, db: AsyncSession, project_id: str) -> list:
        stmt = select(Video).where(Video.project_id == project_id).order_by(Video.create_time.desc())
        result = await db.execute(stmt)
        videos = result.scalars().all()
        return [self._video_to_dict(v) for v in videos]

    async def _upload_image(self, image_content: bytes) -> str:
        return "https://example.com/uploaded_image.jpg"

    def _video_to_dict(self, video: Video) -> Dict[str, Any]:
        return {
            "video_id": video.video_id,
            "project_id": video.project_id,
            "source_image_url": video.source_image_url,
            "file_url": video.file_url,
            "prompt": video.prompt,
            "duration": video.duration,
            "resolution": video.resolution,
            "status": video.status,
            "create_time": video.create_time.isoformat() if video.create_time else None
        }


video_service = VideoService()
