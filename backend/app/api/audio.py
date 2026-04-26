"""
音频模块API路由

提供基于 Qwen TTS 的语音生成、查询、修改与删除接口。
"""

from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logger import app_logger
from app.core.oss import oss_client
from app.core.security import get_current_user
from app.schemas.audio import AudioGenerateRequest, AudioUpdateRequest
from app.schemas.common import APIException, ErrorCode, ResponseModel
from app.services.audio_service import audio_service

router = APIRouter(prefix="/api/audio", tags=["音频模块"])


@router.post("", response_model=ResponseModel, status_code=202)
async def create_audio(
    audio_data: AudioGenerateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    app_logger.info(
        f"创建音频请求: {current_user.get('username')}, storyId={audio_data.storyId}, voiceId={audio_data.voiceId}"
    )
    audio = await audio_service.create_audio_job(
        db=db,
        user_id=current_user["user_id"],
        story_id=audio_data.storyId,
        voice_id=audio_data.voiceId,
        speech_rate=audio_data.speechRate,
    )
    return ResponseModel(code=202, message="任务已创建", data={"audioId": audio.audio_id, "title": audio.title, "storyId": audio.story_id, "status": audio.status, "fileUrl": audio.file_url})


@router.get("", response_model=ResponseModel)
async def get_audio_list(
    storyId: str = Query(..., description="故事章节ID"),
    page: int = Query(1, ge=1, description="第几页"),
    pageSize: int = Query(10, ge=1, le=100, description="每页多少条"),
    title: Optional[str] = Query(None, description="根据语音昵称搜索，支持部分匹配"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    audios, total = await audio_service.list_audios(db, storyId, page, pageSize, title)
    if any(audio.user_id != current_user["user_id"] for audio in audios):
        raise APIException(code=ErrorCode.FORBIDDEN, message="无权限访问该故事的语音列表")
    data = {
        "total": total,
        "lists": [{"audioId": audio.audio_id, "title": audio.title, "status": audio.status, "fileUrl": audio.file_url} for audio in audios],
    }
    return ResponseModel(code=200, message="获取成功", data=data)


@router.put("", response_model=ResponseModel)
async def update_audio(
    audio_data: AudioUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    audio = await audio_service.get_audio_by_id(db, audio_data.audioId)
    if audio is None:
        raise APIException(code=ErrorCode.NOT_FOUND, message="语音不存在")
    if audio.user_id != current_user["user_id"]:
        raise APIException(code=ErrorCode.FORBIDDEN, message="无权限修改此语音")
    await audio_service.update_audio_title(db, audio_data.audioId, audio_data.title)
    return ResponseModel(code=200, message="修改成功", data=None)


@router.get("/{audioId}")
async def get_audio_file(
    audioId: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    audio = await audio_service.get_audio_by_id(db, audioId)
    if audio is None:
        raise APIException(code=ErrorCode.NOT_FOUND, message="语音不存在")
    if audio.user_id != current_user["user_id"]:
        raise APIException(code=ErrorCode.FORBIDDEN, message="无权限访问此语音")
    if not audio.file_url:
        raise APIException(code=ErrorCode.NOT_FOUND, message="语音文件不存在")

    signed_url = oss_client.get_sign_url_from_file_url(audio.file_url)
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(signed_url)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "audio/wav")
        return StreamingResponse(iter([response.content]), media_type=content_type, headers={"Content-Disposition": f'inline; filename="{audio.title}.wav"'})


@router.delete("/{audioId}", response_model=ResponseModel)
async def delete_audio(
    audioId: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    audio = await audio_service.get_audio_by_id(db, audioId)
    if audio is None:
        raise APIException(code=ErrorCode.NOT_FOUND, message="语音不存在")
    if audio.user_id != current_user["user_id"]:
        raise APIException(code=ErrorCode.FORBIDDEN, message="无权限删除此语音")
    await audio_service.delete_audio(db, audioId)
    return ResponseModel(code=200, message="删除成功", data=None)
