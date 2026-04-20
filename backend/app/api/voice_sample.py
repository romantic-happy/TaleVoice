"""
音色样本API路由

提供克隆音频样本的创建、修改、查询、删除等接口
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logger import app_logger
from app.schemas.common import ResponseModel, APIException, ErrorCode
from app.schemas.voice_sample import (
    VoiceSampleCreate,
    VoiceSampleUpdate,
)
from app.services.voice_sample_service import voice_sample_service

router = APIRouter(prefix="/api/user/audio", tags=["用户模块/参考音频"])


@router.post("", response_model=ResponseModel)
async def create_voice_sample(
    voice_data: VoiceSampleCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建音色样本接口

    - 需要JWT认证
    - 创建一个新的音色样本记录
    - 返回音色样本ID
    """
    app_logger.info(f"创建音色样本请求: {current_user.get('username')}, 名称: {voice_data.voiceName}")
    voice_sample = await voice_sample_service.create_voice_sample(
        db,
        current_user["user_id"],
        voice_data.voiceName
    )
    app_logger.info(f"创建音色样本成功: {voice_sample.voice_id}")
    return ResponseModel(code=200, message="创建成功", data=voice_sample.voice_id)


@router.put("", response_model=ResponseModel)
async def update_voice_sample(
    voice_data: VoiceSampleUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    修改音色样本名称接口

    - 需要JWT认证
    - 只能修改属于自己的音色样本
    """
    app_logger.info(f"更新音色样本请求: {current_user.get('username')}, ID: {voice_data.voiceId}")
    voice_sample = await voice_sample_service.get_voice_sample_by_id(db, voice_data.voiceId)
    if not voice_sample:
        app_logger.error(f"更新音色样本失败-不存在: {voice_data.voiceId}")
        raise APIException(code=ErrorCode.NOT_FOUND, message="音色样本不存在")
    if voice_sample.user_id != current_user["user_id"]:
        app_logger.warning(f"更新音色样本失败-无权限: {current_user.get('username')}, ID: {voice_data.voiceId}")
        raise APIException(code=ErrorCode.FORBIDDEN, message="无权限修改此音色样本")
    await voice_sample_service.update_voice_sample(db, voice_data.voiceId, voice_data.voiceName)
    app_logger.info(f"更新音色样本成功: {voice_data.voiceId}")
    return ResponseModel(code=200, message="修改成功", data=None)


@router.get("", response_model=ResponseModel)
async def get_voice_samples(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取音色样本列表接口

    - 需要JWT认证
    - 返回当前用户的所有音色样本
    """
    voice_samples = await voice_sample_service.get_voice_samples_by_user(db, current_user["user_id"])
    data = [
        {
            "voiceId": vs.voice_id,
            "voiceName": vs.voice_name,
            "default": bool(vs.is_default)
        }
        for vs in voice_samples
    ]
    app_logger.info(f"获取音色样本列表: {current_user.get('username')}, 数量: {len(data)}")
    return ResponseModel(code=200, message="获取成功", data=data)


@router.delete("/{voice_id}", response_model=ResponseModel)
async def delete_voice_sample(
    voice_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除音色样本接口

    - 需要JWT认证
    - 只能删除属于自己的音色样本
    """
    app_logger.info(f"删除音色样本请求: {current_user.get('username')}, ID: {voice_id}")
    voice_sample = await voice_sample_service.get_voice_sample_by_id(db, voice_id)
    if not voice_sample:
        app_logger.error(f"删除音色样本失败-不存在: {voice_id}")
        raise APIException(code=ErrorCode.NOT_FOUND, message="音色样本不存在")
    if voice_sample.user_id != current_user["user_id"]:
        app_logger.warning(f"删除音色样本失败-无权限: {current_user.get('username')}, ID: {voice_id}")
        raise APIException(code=ErrorCode.FORBIDDEN, message="无权限删除此音色样本")
    await voice_sample_service.delete_voice_sample(db, voice_id)
    app_logger.info(f"删除音色样本成功: {voice_id}")
    return ResponseModel(code=200, message="删除成功", data=None)
