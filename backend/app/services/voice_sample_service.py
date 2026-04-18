"""
音色样本服务层

处理音色样本相关的业务逻辑，包括创建、更新、删除和查询音色样本
"""

import uuid
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import VoiceSample
from app.models.user import User


class VoiceSampleService:
    """音色样本服务类，提供音色样本相关的业务逻辑处理"""

    @staticmethod
    async def get_voice_sample_by_id(db: AsyncSession, voice_id: str) -> Optional[VoiceSample]:
        """
        根据音色ID查询音色样本

        Args:
            db: 数据库会话
            voice_id: 音色样本ID

        Returns:
            Optional[VoiceSample]: 找到返回VoiceSample对象，否则返回None
        """
        result = await db.execute(select(VoiceSample).where(VoiceSample.voice_id == voice_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_voice_samples_by_user(db: AsyncSession, user_id: str) -> List[VoiceSample]:
        """
        获取用户的所有音色样本

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            List[VoiceSample]: 音色样本列表
        """
        result = await db.execute(select(VoiceSample).where(VoiceSample.user_id == user_id))
        return result.scalars().all()

    @staticmethod
    async def create_voice_sample(db: AsyncSession, user_id: str, voice_name: Optional[str] = None) -> VoiceSample:
        """
        创建新的音色样本

        Args:
            db: 数据库会话
            user_id: 所属用户ID
            voice_name: 音色名称，不提供则使用"默认音色"

        Returns:
            VoiceSample: 创建的音色样本对象
        """
        voice_sample = VoiceSample(
            voice_id=str(uuid.uuid4()),
            voice_name=voice_name or "默认音色",
            user_id=user_id
        )
        db.add(voice_sample)
        await db.commit()
        await db.refresh(voice_sample)
        return voice_sample

    @staticmethod
    async def update_voice_sample(db: AsyncSession, voice_id: str, voice_name: str) -> Optional[VoiceSample]:
        """
        更新音色样本名称

        Args:
            db: 数据库会话
            voice_id: 音色样本ID
            voice_name: 新的音色名称

        Returns:
            Optional[VoiceSample]: 更新成功返回音色样本对象，不存在返回None
        """
        voice_sample = await VoiceSampleService.get_voice_sample_by_id(db, voice_id)
        if not voice_sample:
            return None
        voice_sample.voice_name = voice_name
        await db.commit()
        await db.refresh(voice_sample)
        return voice_sample

    @staticmethod
    async def delete_voice_sample(db: AsyncSession, voice_id: str) -> bool:
        """
        删除音色样本

        Args:
            db: 数据库会话
            voice_id: 音色样本ID

        Returns:
            bool: 删除成功返回True，不存在返回False
        """
        voice_sample = await VoiceSampleService.get_voice_sample_by_id(db, voice_id)
        if not voice_sample:
            return False
        await db.delete(voice_sample)
        await db.commit()
        return True


voice_sample_service = VoiceSampleService()
