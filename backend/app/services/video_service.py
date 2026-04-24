"""
视频生成核心服务层

处理视频生成的完整业务逻辑，包括：
- 视频CRUD操作
- AI视频生成任务管理
- 背景音乐配置
- 生成状态轮询与回调
"""

import uuid
from typing import Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.video import Video, BGM
from app.services.ai_provider import ai_provider, VideoGenerationResult
from app.services.prompt_engine import prompt_engine
from app.services.bgm_service import bgm_processor
from app.core.logger import app_logger


VIDEO_STATUS_MAP = {
    0: "pending",
    1: "processing",
    2: "completed",
    3: "failed"
}


class VideoService:
    """
    视频服务类

    提供视频生成、查询、更新、删除等业务逻辑
    协调AI适配器、提示词引擎、背景音乐处理器等组件
    """

    @staticmethod
    async def get_video_by_id(db: AsyncSession, video_id: str) -> Optional[Video]:
        """
        根据视频ID查询视频

        Args:
            db: 数据库会话
            video_id: 视频ID

        Returns:
            Optional[Video]: 找到返回Video对象，否则返回None
        """
        result = await db.execute(select(Video).where(Video.video_id == video_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_videos_by_project(
        db: AsyncSession,
        project_id: str,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[Video], int]:
        """
        获取项目下的视频列表(分页)

        Args:
            db: 数据库会话
            project_id: 项目ID
            page: 页码
            page_size: 每页数量

        Returns:
            Tuple[List[Video], int]: 视频列表和总数
        """
        query = select(Video).where(Video.project_id == project_id)

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        paginated_query = query.order_by(Video.create_time.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size)
        result = await db.execute(paginated_query)
        videos = result.scalars().all()

        return videos, total

    @staticmethod
    async def get_videos_by_user(
        db: AsyncSession,
        user_id: str,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[Video], int]:
        """
        获取用户的视频列表(分页)

        Args:
            db: 数据库会话
            user_id: 用户ID
            page: 页码
            page_size: 每页数量

        Returns:
            Tuple[List[Video], int]: 视频列表和总数
        """
        query = select(Video).where(Video.user_id == user_id)

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        paginated_query = query.order_by(Video.create_time.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size)
        result = await db.execute(paginated_query)
        videos = result.scalars().all()

        return videos, total

    @staticmethod
    async def create_video(
        db: AsyncSession,
        user_id: str,
        project_id: str,
        title: str,
        source_image_url: str,
        description: Optional[str] = None,
        prompt: Optional[str] = None,
        bgm_id: Optional[str] = None,
        bgm_volume: int = 30,
        bgm_fade_in: float = 1.0,
        bgm_fade_out: float = 1.5,
        bgm_loop: bool = True
    ) -> Video:
        """
        创建视频生成任务

        创建视频记录并提交AI生成任务

        Args:
            db: 数据库会话
            user_id: 用户ID
            project_id: 项目ID
            title: 视频标题
            source_image_url: 源图片URL
            description: 视频描述
            prompt: 自定义提示词
            bgm_id: 背景音乐ID
            bgm_volume: 背景音乐音量
            bgm_fade_in: 淡入时长
            bgm_fade_out: 淡出时长
            bgm_loop: 是否循环播放

        Returns:
            Video: 创建的视频对象
        """
        video = Video(
            video_id=str(uuid.uuid4()),
            user_id=user_id,
            project_id=project_id,
            title=title,
            description=description,
            source_image_url=source_image_url,
            prompt=prompt,
            bgm_id=bgm_id,
            bgm_volume=bgm_volume,
            bgm_fade_in=str(bgm_fade_in),
            bgm_fade_out=str(bgm_fade_out),
            bgm_loop=1 if bgm_loop else 0,
            status=0
        )
        db.add(video)
        await db.commit()
        await db.refresh(video)

        app_logger.info(f"视频生成任务已创建: {video.video_id}")

        return video

    @staticmethod
    async def start_video_generation(video: Video) -> VideoGenerationResult:
        """
        启动AI视频生成

        调用AI适配器提交视频生成任务

        Args:
            video: 视频对象

        Returns:
            VideoGenerationResult: AI生成结果
        """
        prompt_result = prompt_engine.optimize(
            text=video.description or video.title,
            custom_prompt=video.prompt
        )

        app_logger.info(
            f"启动AI视频生成: video_id={video.video_id}, "
            f"prompt={prompt_result.optimized_prompt[:100]}..."
        )

        result = await ai_provider.generate_video(
            image_url=video.source_image_url,
            prompt=prompt_result.optimized_prompt
        )

        return result

    @staticmethod
    async def update_video_status(
        db: AsyncSession,
        video_id: str,
        status: int,
        file_url: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        duration: Optional[int] = None,
        resolution: Optional[str] = None,
        fps: Optional[int] = None,
        file_size: Optional[int] = None
    ) -> Optional[Video]:
        """
        更新视频状态和属性

        Args:
            db: 数据库会话
            video_id: 视频ID
            status: 状态码(0=pending, 1=processing, 2=completed, 3=failed)
            file_url: 视频文件URL
            thumbnail_url: 缩略图URL
            duration: 时长(秒)
            resolution: 分辨率
            fps: 帧率
            file_size: 文件大小(字节)

        Returns:
            Optional[Video]: 更新后的视频对象，不存在返回None
        """
        video = await VideoService.get_video_by_id(db, video_id)
        if not video:
            return None

        video.status = status
        if file_url is not None:
            video.file_url = file_url
        if thumbnail_url is not None:
            video.thumbnail_url = thumbnail_url
        if duration is not None:
            video.duration = duration
        if resolution is not None:
            video.resolution = resolution
        if fps is not None:
            video.fps = fps
        if file_size is not None:
            video.file_size = file_size

        await db.commit()
        await db.refresh(video)

        app_logger.info(f"视频状态更新: video_id={video_id}, status={VIDEO_STATUS_MAP.get(status, 'unknown')}")
        return video

    @staticmethod
    async def update_video(
        db: AsyncSession,
        video_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[Video]:
        """
        更新视频信息

        Args:
            db: 数据库会话
            video_id: 视频ID
            title: 新标题
            description: 新描述

        Returns:
            Optional[Video]: 更新后的视频对象，不存在返回None
        """
        video = await VideoService.get_video_by_id(db, video_id)
        if not video:
            return None

        if title is not None:
            video.title = title
        if description is not None:
            video.description = description

        await db.commit()
        await db.refresh(video)
        return video

    @staticmethod
    async def delete_video(db: AsyncSession, video_id: str) -> bool:
        """
        删除视频

        Args:
            db: 数据库会话
            video_id: 视频ID

        Returns:
            bool: 删除成功返回True，不存在返回False
        """
        video = await VideoService.get_video_by_id(db, video_id)
        if not video:
            return False

        await db.delete(video)
        await db.commit()
        app_logger.info(f"视频已删除: {video_id}")
        return True

    @staticmethod
    async def configure_bgm(
        db: AsyncSession,
        video_id: str,
        bgm_id: str,
        volume: int = 30,
        fade_in: float = 1.0,
        fade_out: float = 1.5,
        loop: bool = True
    ) -> Optional[Video]:
        """
        配置视频的背景音乐

        Args:
            db: 数据库会话
            video_id: 视频ID
            bgm_id: 背景音乐ID
            volume: 音量百分比(0-100)
            fade_in: 淡入时长(秒)
            fade_out: 淡出时长(秒)
            loop: 是否循环播放

        Returns:
            Optional[Video]: 更新后的视频对象，不存在返回None
        """
        video = await VideoService.get_video_by_id(db, video_id)
        if not video:
            return None

        video.bgm_id = bgm_id
        video.bgm_volume = volume
        video.bgm_fade_in = str(fade_in)
        video.bgm_fade_out = str(fade_out)
        video.bgm_loop = 1 if loop else 0

        await db.commit()
        await db.refresh(video)

        app_logger.info(f"视频背景音乐配置更新: video_id={video_id}, bgm_id={bgm_id}")
        return video


class BGMService:
    """
    背景音乐服务类

    提供背景音乐的CRUD操作和推荐功能
    """

    @staticmethod
    async def get_bgm_by_id(db: AsyncSession, bgm_id: str) -> Optional[BGM]:
        """
        根据ID查询背景音乐

        Args:
            db: 数据库会话
            bgm_id: 背景音乐ID

        Returns:
            Optional[BGM]: 找到返回BGM对象，否则返回None
        """
        result = await db.execute(select(BGM).where(BGM.bgm_id == bgm_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_bgm_list(
        db: AsyncSession,
        source: Optional[str] = None,
        style: Optional[str] = None,
        emotion: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[BGM], int]:
        """
        获取背景音乐列表(分页)

        Args:
            db: 数据库会话
            source: 来源筛选(system/user)
            style: 风格筛选
            emotion: 情感筛选
            page: 页码
            page_size: 每页数量

        Returns:
            Tuple[List[BGM], int]: 音乐列表和总数
        """
        query = select(BGM)

        if source:
            query = query.where(BGM.source == source)
        if style:
            query = query.where(BGM.style == style)
        if emotion:
            query = query.where(BGM.emotion == emotion)

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        paginated_query = query.order_by(BGM.play_count.desc(), BGM.create_time.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size)
        result = await db.execute(paginated_query)
        bgms = result.scalars().all()

        return bgms, total

    @staticmethod
    async def create_bgm(
        db: AsyncSession,
        name: str,
        file_url: str,
        source: str = "user",
        user_id: Optional[str] = None,
        style: Optional[str] = None,
        emotion: Optional[str] = None,
        duration: Optional[int] = None,
        bpm: Optional[int] = None,
        format: str = "mp3",
        sample_rate: Optional[int] = None,
        channels: Optional[int] = None,
        bit_rate: Optional[int] = None,
        file_size: Optional[int] = None
    ) -> BGM:
        """
        创建背景音乐记录

        Args:
            db: 数据库会话
            name: 音乐名称
            file_url: 文件URL
            source: 来源(system/user)
            user_id: 用户ID(用户上传时必填)
            style: 风格标签
            emotion: 情感标签
            duration: 时长(秒)
            bpm: BPM
            format: 音频格式
            sample_rate: 采样率
            channels: 声道数
            bit_rate: 比特率
            file_size: 文件大小(字节)

        Returns:
            BGM: 创建的背景音乐对象
        """
        bgm = BGM(
            bgm_id=str(uuid.uuid4()),
            name=name,
            file_url=file_url,
            source=source,
            user_id=user_id,
            style=style,
            emotion=emotion,
            duration=duration,
            bpm=bpm,
            format=format,
            sample_rate=sample_rate,
            channels=channels,
            bit_rate=bit_rate,
            file_size=file_size
        )
        db.add(bgm)
        await db.commit()
        await db.refresh(bgm)

        app_logger.info(f"背景音乐已创建: {bgm.bgm_id}, name={name}")
        return bgm

    @staticmethod
    async def recommend_bgm(
        db: AsyncSession,
        emotion: str,
        limit: int = 10
    ) -> List[BGM]:
        """
        根据情感标签推荐背景音乐

        按情感匹配度和播放热度排序推荐

        Args:
            db: 数据库会话
            emotion: 情感标签
            limit: 返回数量

        Returns:
            List[BGM]: 推荐的背景音乐列表
        """
        query = select(BGM).where(BGM.emotion == emotion) \
            .order_by(BGM.play_count.desc()) \
            .limit(limit)
        result = await db.execute(query)
        bgms = result.scalars().all()

        if len(bgms) < limit:
            fallback_query = select(BGM) \
                .order_by(BGM.play_count.desc()) \
                .limit(limit - len(bgms))
            fallback_result = await db.execute(fallback_query)
            bgms.extend(fallback_result.scalars().all())

        return bgms

    @staticmethod
    async def delete_bgm(db: AsyncSession, bgm_id: str) -> bool:
        """
        删除背景音乐

        Args:
            db: 数据库会话
            bgm_id: 背景音乐ID

        Returns:
            bool: 删除成功返回True，不存在返回False
        """
        bgm = await BGMService.get_bgm_by_id(db, bgm_id)
        if not bgm:
            return False

        await db.delete(bgm)
        await db.commit()
        app_logger.info(f"背景音乐已删除: {bgm_id}")
        return True


video_service = VideoService()
bgm_service = BGMService()
