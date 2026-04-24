"""
视频模块API路由

提供视频生成、查询、更新、删除及背景音乐配置等接口
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logger import app_logger
from app.schemas.common import ResponseModel, APIException, ErrorCode
from app.schemas.video import (
    VideoCreate,
    VideoUpdate,
    VideoBGMConfig,
    VideoResponse,
    VideoListItem,
    VideoListData,
    VideoListResponse,
    VideoErrorCode,
    VIDEO_STATUS_MAP,
)
from app.services.video_service import video_service

router = APIRouter(prefix="/api/video", tags=["视频模块"])


@router.post("", response_model=ResponseModel)
async def create_video(
    video_data: VideoCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建视频生成任务接口

    - 需要JWT认证
    - 提交图片URL和提示词，创建AI视频生成任务
    - 返回视频ID，视频异步生成

    请求参数:
    - project_id: 项目ID(必填)
    - title: 视频标题(必填)
    - source_image_url: 源图片URL(必填)
    - description: 视频描述(可选)
    - prompt: 自定义提示词(可选)
    - bgm_id: 背景音乐ID(可选)
    - bgm_volume: 音量0-100(默认30)
    - bgm_fade_in: 淡入时长0-5秒(默认1.0)
    - bgm_fade_out: 淡出时长0-5秒(默认1.5)
    - bgm_loop: 是否循环(默认true)
    """
    app_logger.info(f"创建视频请求: user={current_user.get('username')}, title={video_data.title}")

    video = await video_service.create_video(
        db,
        current_user["user_id"],
        video_data.project_id,
        video_data.title,
        video_data.source_image_url,
        video_data.description,
        video_data.prompt,
        video_data.bgm_id,
        video_data.bgm_volume,
        video_data.bgm_fade_in,
        video_data.bgm_fade_out,
        video_data.bgm_loop
    )

    try:
        generation_result = await video_service.start_video_generation(video)
        if generation_result.status == "failed":
            await video_service.update_video_status(
                db, video.video_id, status=3
            )
            raise APIException(
                code=VideoErrorCode.AI_SERVICE_UNAVAILABLE,
                message=f"AI视频生成服务不可用: {generation_result.error_message}"
            )

        await video_service.update_video_status(
            db, video.video_id, status=1
        )
    except APIException:
        raise
    except Exception as e:
        app_logger.error(f"启动视频生成失败: {str(e)}")
        await video_service.update_video_status(
            db, video.video_id, status=3
        )

    app_logger.info(f"视频生成任务已创建: {video.video_id}")
    return ResponseModel(code=200, message="视频生成任务已创建", data=video.video_id)


@router.get("/list", response_model=VideoListResponse)
async def get_video_list(
    project_id: Optional[str] = Query(None, description="项目ID筛选"),
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取视频列表接口

    - 需要JWT认证
    - 返回当前用户的视频列表(分页)
    - 可按项目ID筛选
    """
    app_logger.info(f"获取视频列表: user={current_user.get('username')}, project_id={project_id}")

    if project_id:
        videos, total = await video_service.get_videos_by_project(
            db, project_id, page, pageSize
        )
    else:
        videos, total = await video_service.get_videos_by_user(
            db, current_user["user_id"], page, pageSize
        )

    lists = [
        VideoListItem(
            video_id=v.video_id,
            project_id=v.project_id,
            title=v.title,
            thumbnail_url=v.thumbnail_url,
            duration=v.duration,
            status=v.status,
            status_text=VIDEO_STATUS_MAP.get(v.status, "unknown"),
            create_time=v.create_time
        )
        for v in videos
    ]

    app_logger.info(f"获取视频列表成功: 总数={total}")
    return VideoListResponse(
        code=200,
        message="获取成功",
        data=VideoListData(total=total, lists=lists)
    )


@router.get("/{video_id}", response_model=ResponseModel)
async def get_video_detail(
    video_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取视频详情接口

    - 需要JWT认证
    - 只能查看属于自己的视频
    """
    video = await video_service.get_video_by_id(db, video_id)
    if not video:
        raise APIException(code=VideoErrorCode.VIDEO_NOT_FOUND, message="视频不存在")

    if video.user_id != current_user["user_id"]:
        raise APIException(code=VideoErrorCode.VIDEO_NO_PERMISSION, message="无权限查看此视频")

    response_data = VideoResponse(
        video_id=video.video_id,
        project_id=video.project_id,
        user_id=video.user_id,
        title=video.title,
        description=video.description,
        source_image_url=video.source_image_url,
        file_url=video.file_url,
        thumbnail_url=video.thumbnail_url,
        duration=video.duration,
        resolution=video.resolution,
        fps=video.fps,
        file_size=video.file_size,
        format=video.format,
        status=video.status,
        status_text=VIDEO_STATUS_MAP.get(video.status, "unknown"),
        prompt=video.prompt,
        bgm_id=video.bgm_id,
        bgm_volume=video.bgm_volume,
        bgm_fade_in=video.bgm_fade_in,
        bgm_fade_out=video.bgm_fade_out,
        bgm_loop=video.bgm_loop,
        create_time=video.create_time,
        update_time=video.update_time
    )

    return ResponseModel(code=200, message="获取成功", data=response_data.model_dump())


@router.put("", response_model=ResponseModel)
async def update_video(
    video_data: VideoUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新视频信息接口

    - 需要JWT认证
    - 只能修改属于自己的视频
    """
    video = await video_service.get_video_by_id(db, video_data.video_id)
    if not video:
        raise APIException(code=VideoErrorCode.VIDEO_NOT_FOUND, message="视频不存在")

    if video.user_id != current_user["user_id"]:
        raise APIException(code=VideoErrorCode.VIDEO_NO_PERMISSION, message="无权限修改此视频")

    await video_service.update_video(
        db, video_data.video_id, video_data.title, video_data.description
    )

    return ResponseModel(code=200, message="修改成功", data=None)


@router.delete("/{video_id}", response_model=ResponseModel)
async def delete_video(
    video_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除视频接口

    - 需要JWT认证
    - 只能删除属于自己的视频
    """
    video = await video_service.get_video_by_id(db, video_id)
    if not video:
        raise APIException(code=VideoErrorCode.VIDEO_NOT_FOUND, message="视频不存在")

    if video.user_id != current_user["user_id"]:
        raise APIException(code=VideoErrorCode.VIDEO_NO_PERMISSION, message="无权限删除此视频")

    await video_service.delete_video(db, video_id)
    return ResponseModel(code=200, message="删除成功", data=None)


@router.post("/{video_id}/bgm", response_model=ResponseModel)
async def configure_video_bgm(
    video_id: str,
    bgm_config: VideoBGMConfig,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    配置视频背景音乐接口

    - 需要JWT认证
    - 只能配置属于自己的视频
    - 设置背景音乐ID、音量、淡入淡出、循环等参数

    请求参数:
    - bgm_id: 背景音乐ID(必填)
    - volume: 音量0-100(默认30)
    - fade_in: 淡入时长0-5秒(默认1.0)
    - fade_out: 淡出时长0-5秒(默认1.5)
    - loop: 是否循环(默认true)
    - start_offset: 起始偏移(默认0.0)
    - sync_mode: 同步模式auto/manual(默认auto)
    """
    video = await video_service.get_video_by_id(db, video_id)
    if not video:
        raise APIException(code=VideoErrorCode.VIDEO_NOT_FOUND, message="视频不存在")

    if video.user_id != current_user["user_id"]:
        raise APIException(code=VideoErrorCode.VIDEO_NO_PERMISSION, message="无权限操作此视频")

    updated_video = await video_service.configure_bgm(
        db, video_id,
        bgm_config.bgm_id,
        bgm_config.volume,
        bgm_config.fade_in,
        bgm_config.fade_out,
        bgm_config.loop
    )

    if not updated_video:
        raise APIException(code=VideoErrorCode.BGM_NOT_FOUND, message="背景音乐不存在")

    return ResponseModel(code=200, message="背景音乐配置成功", data=None)


@router.post("/{video_id}/retry", response_model=ResponseModel)
async def retry_video_generation(
    video_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    重试视频生成接口

    - 需要JWT认证
    - 只能重试属于自己的失败视频
    - 重新提交AI生成任务
    """
    video = await video_service.get_video_by_id(db, video_id)
    if not video:
        raise APIException(code=VideoErrorCode.VIDEO_NOT_FOUND, message="视频不存在")

    if video.user_id != current_user["user_id"]:
        raise APIException(code=VideoErrorCode.VIDEO_NO_PERMISSION, message="无权限操作此视频")

    if video.status != 3:
        raise APIException(code=VideoErrorCode.VIDEO_ALREADY_PROCESSING, message="只能重试生成失败的视频")

    try:
        generation_result = await video_service.start_video_generation(video)
        if generation_result.status == "failed":
            raise APIException(
                code=VideoErrorCode.AI_SERVICE_UNAVAILABLE,
                message=f"AI视频生成服务不可用: {generation_result.error_message}"
            )

        await video_service.update_video_status(db, video_id, status=1)
    except APIException:
        raise
    except Exception as e:
        app_logger.error(f"重试视频生成失败: {str(e)}")
        await video_service.update_video_status(db, video_id, status=3)

    return ResponseModel(code=200, message="视频生成任务已重新提交", data=None)
