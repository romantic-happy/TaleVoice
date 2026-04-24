"""
背景音乐模块API路由

提供背景音乐列表查询、推荐、上传、删除等接口
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logger import app_logger
from app.core.oss import oss_client
from app.schemas.common import ResponseModel, APIException, ErrorCode
from app.schemas.video import (
    BGMListItem,
    BGMListData,
    BGMListResponse,
    BGMRecommendResponse,
    VideoErrorCode,
)
from app.services.video_service import bgm_service
from app.services.bgm_service import bgm_processor

router = APIRouter(prefix="/api/bgm", tags=["背景音乐模块"])


@router.get("/list", response_model=BGMListResponse)
async def get_bgm_list(
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(20, ge=1, le=100, description="每页数量"),
    source: Optional[str] = Query(None, description="来源筛选: system/user"),
    style: Optional[str] = Query(None, description="风格筛选"),
    emotion: Optional[str] = Query(None, description="情感筛选"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取背景音乐列表接口

    - 需要JWT认证
    - 返回系统预置和用户上传的背景音乐列表
    - 支持按来源、风格、情感筛选
    """
    app_logger.info(f"获取背景音乐列表: user={current_user.get('username')}")

    bgms, total = await bgm_service.get_bgm_list(
        db, source=source, style=style, emotion=emotion,
        page=page, page_size=pageSize
    )

    lists = [
        BGMListItem(
            bgm_id=b.bgm_id,
            name=b.name,
            source=b.source,
            style=b.style,
            emotion=b.emotion,
            duration=b.duration,
            sample_url=b.sample_url,
            bpm=b.bpm
        )
        for b in bgms
    ]

    return BGMListResponse(
        code=200,
        message="获取成功",
        data=BGMListData(total=total, lists=lists)
    )


@router.get("/recommend", response_model=BGMRecommendResponse)
async def recommend_bgm(
    emotion: str = Query(..., description="情感标签: 温馨/欢快/紧张/神秘/悲伤"),
    limit: int = Query(10, ge=1, le=20, description="返回数量"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取背景音乐推荐列表接口

    - 需要JWT认证
    - 根据情感标签推荐匹配的背景音乐
    - 按播放热度和匹配度排序
    """
    app_logger.info(f"获取背景音乐推荐: emotion={emotion}, limit={limit}")

    bgms = await bgm_service.recommend_bgm(db, emotion=emotion, limit=limit)

    lists = [
        BGMListItem(
            bgm_id=b.bgm_id,
            name=b.name,
            source=b.source,
            style=b.style,
            emotion=b.emotion,
            duration=b.duration,
            sample_url=b.sample_url,
            bpm=b.bpm
        )
        for b in bgms
    ]

    return BGMRecommendResponse(
        code=200,
        message="获取成功",
        data=BGMListData(total=len(lists), lists=lists)
    )


@router.post("/upload", response_model=ResponseModel)
async def upload_bgm(
    file: UploadFile = File(..., description="音频文件(MP3/WAV/AAC/OGG/FLAC)"),
    name: str = Form(..., description="音乐名称"),
    style: Optional[str] = Form(None, description="音乐风格标签"),
    emotion: Optional[str] = Form(None, description="情感标签"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    上传背景音乐接口

    - 需要JWT认证
    - 支持MP3/WAV/AAC/OGG/FLAC格式
    - 文件大小限制20MB
    - 时长限制10秒-10分钟

    错误码:
    - 6001: 不支持的音频格式
    - 6002: 文件大小超限
    - 6003: 音频时长不符合要求
    - 6004: 音频文件损坏
    """
    if not bgm_processor.validate_format(file.filename):
        raise APIException(
            code=VideoErrorCode.BGM_INVALID_FORMAT,
            message=f"不支持的音频格式，允许格式: MP3/WAV/AAC/OGG/FLAC"
        )

    file_content = await file.read()
    file_size = len(file_content)

    if not bgm_processor.validate_file_size(file_size):
        raise APIException(
            code=VideoErrorCode.BGM_FILE_TOO_LARGE,
            message=f"文件大小超限，最大允许20MB"
        )

    ext = file.filename.rsplit(".", 1)[-1].lower()
    file_url = oss_client.upload_file(file_content, f".{ext}", "bgm/user/")

    duration = None
    sample_rate = None
    channels = None
    bit_rate = None

    bgm = await bgm_service.create_bgm(
        db,
        name=name,
        file_url=file_url,
        source="user",
        user_id=current_user["user_id"],
        style=style,
        emotion=emotion,
        duration=duration,
        format=ext,
        sample_rate=sample_rate,
        channels=channels,
        bit_rate=bit_rate,
        file_size=file_size
    )

    app_logger.info(f"背景音乐上传成功: {bgm.bgm_id}, name={name}")
    return ResponseModel(code=200, message="上传成功", data={
        "bgm_id": bgm.bgm_id,
        "name": bgm.name,
        "url": bgm.file_url,
        "duration": bgm.duration,
        "format": bgm.format,
        "file_size": bgm.file_size
    })


@router.delete("/{bgm_id}", response_model=ResponseModel)
async def delete_bgm(
    bgm_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除背景音乐接口

    - 需要JWT认证
    - 只能删除自己上传的背景音乐
    - 系统预置音乐不可删除
    """
    bgm = await bgm_service.get_bgm_by_id(db, bgm_id)
    if not bgm:
        raise APIException(code=VideoErrorCode.BGM_NOT_FOUND, message="背景音乐不存在")

    if bgm.source == "system":
        raise APIException(code=ErrorCode.FORBIDDEN, message="系统预置音乐不可删除")

    if bgm.user_id != current_user["user_id"]:
        raise APIException(code=ErrorCode.FORBIDDEN, message="无权限删除此背景音乐")

    await bgm_service.delete_bgm(db, bgm_id)
    return ResponseModel(code=200, message="删除成功", data=None)
