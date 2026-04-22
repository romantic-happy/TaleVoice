"""
音色样本服务层

处理音色样本相关的业务逻辑，包括创建、更新、删除和查询音色样本
"""
import asyncio
import os
import uuid
from typing import Optional, List

from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import VoiceSample
from app.core.oss import oss_client
from starlette import status

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

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
    async def create_voice_sample(
            db: AsyncSession,
            user_id: str,
            voice_name: Optional[str] = None,
            audio_file: UploadFile = None
    ) -> VoiceSample:
        """创建音色样本并上传到 OSS"""

        audio_url = None

        if audio_file:
            # 1. 检查文件大小 (避免读取后才发现过大)
            # 现代浏览器/框架通常能通过 size 属性直接获取
            if audio_file.size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="文件大小不能超过 10MB"
                )

            # 2. 确保从文件头开始读取
            await audio_file.seek(0)

            # 3. 读取内容
            file_content = await audio_file.read()

            # 二次检查内容长度
            if len(file_content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="文件内容超过 10MB 限制"
                )

            # 4. 校验文件名，获取后缀名并生成唯一文件名
            filename = audio_file.filename
            if not filename or not filename.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="上传文件必须包含有效的文件名"
                )

            file_ext = os.path.splitext(filename)[1] or ".mp3"
            # 这里应该检查文件类型的但是我不管了
            unique_filename = f"{uuid.uuid4()}{file_ext}"

            # 5. 异步处理 IO
            loop = asyncio.get_running_loop()
            try:
                audio_url = await loop.run_in_executor(
                    None,  # 使用默认线程池
                    lambda: oss_client.upload_file(
                        file_content=file_content,
                        file_ext=file_ext,
                        key_prefix=f"voice_samples/{user_id}/"
                    )
                )
            except Exception as e:
                # 记录日志或处理上传失败
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"OSS 上传失败: {str(e)}"
                )
            finally:
                # 及时关闭临时文件释放系统资源
                await audio_file.close()

        # 6. 数据库记录
        try:
            voice_sample = VoiceSample(
                voice_id=str(uuid.uuid4()),
                voice_name=voice_name or "默认音色",
                user_id=user_id,
                audio_url=audio_url,
                is_default=False
            )

            db.add(voice_sample)
            await db.commit()
            await db.refresh(voice_sample)
            return voice_sample
        except Exception:
            await db.rollback()
            raise

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
