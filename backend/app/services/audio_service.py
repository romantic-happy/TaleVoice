"""
音频服务层

负责基于 Qwen TTS 生成语音、写入数据库并上传 OSS。
"""

import asyncio
import io
import uuid
from dataclasses import dataclass
from typing import Optional

import soundfile as sf
import torch
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logger import app_logger
from app.core.oss import oss_client
from app.models import Audio, Project, Story, VoiceSample


@dataclass
class GeneratedAudio:
    wav_bytes: bytes


class AudioService:
    def __init__(self) -> None:
        self._model = None
        self._model_lock = asyncio.Lock()

    def _device_and_dtype(self) -> tuple[str, torch.dtype]:
        if settings.TTS_DEVICE.lower() == "cuda" and torch.cuda.is_available():
            return settings.TTS_DEVICE, torch.bfloat16
        return "cpu", torch.float32

    async def _get_model(self):
        async with self._model_lock:
            if self._model is not None:
                return self._model
            try:
                from qwen_tts import Qwen3TTSModel
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"Qwen TTS 依赖加载失败: {exc}") from exc

            device, dtype = self._device_and_dtype()
            self._model = Qwen3TTSModel.from_pretrained(
                settings.TTS_MODEL_NAME,
                device_map=device,
                dtype=dtype,
                attn_implementation=settings.TTS_ATTENTION_IMPLEMENTATION,
            )
            return self._model

    async def _load_reference_audio(self, voice_sample: VoiceSample) -> str:
        if not voice_sample.audio_url:
            raise HTTPException(status_code=400, detail="参考音频不存在")
        try:
            return oss_client.get_sign_url_from_file_url(voice_sample.audio_url, expires=3600)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"参考音频签名URL生成失败: {exc}") from exc

    async def _get_voice_sample_data(self, db: AsyncSession, voice_id: str, user_id: str) -> tuple[str, Optional[str]]:
        voice_sample = await db.get(VoiceSample, voice_id)
        if voice_sample is None:
            raise HTTPException(status_code=404, detail=f"音色样本不存在: {voice_id}")
        if voice_sample.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权限使用此音色样本")
        ref_audio = await self._load_reference_audio(voice_sample)
        ref_text = voice_sample.voice_name or None
        return ref_audio, ref_text

    async def _generate_wav(self, text: str, ref_audio: str, ref_text: Optional[str], language: str) -> GeneratedAudio:
        model = await self._get_model()

        def _run():
            kwargs = {"text": text, "language": language, "ref_audio": ref_audio}
            if ref_text:
                kwargs["ref_text"] = ref_text
            wavs, sr = model.generate_voice_clone(**kwargs)
            buffer = io.BytesIO()
            sf.write(buffer, wavs[0], sr, format="WAV")
            return GeneratedAudio(wav_bytes=buffer.getvalue())

        return await asyncio.get_running_loop().run_in_executor(None, _run)

    async def _upload_audio(self, wav_bytes: bytes) -> str:
        def _run():
            return oss_client.upload_file(wav_bytes, ".wav", key_prefix="audio/")

        return await asyncio.get_running_loop().run_in_executor(None, _run)

    async def _process_audio_job(self, audio_id: str, story_text: str, voice_url: str, ref_text: Optional[str]) -> None:
        async with AsyncSessionLocal() as session:
            try:
                generated = await self._generate_wav(story_text, voice_url, ref_text, settings.TTS_LANGUAGE)
                file_url = await self._upload_audio(generated.wav_bytes)
                audio = await session.get(Audio, audio_id)
                if audio is None:
                    return
                audio.file_url = file_url
                audio.status = 1
                await session.commit()
            except Exception as exc:
                audio = await session.get(Audio, audio_id)
                if audio is not None:
                    audio.status = 2
                    await session.commit()
                app_logger.error(f"音频异步生成失败: {exc}", exc_info=True)

    async def create_audio_job(self, db: AsyncSession, user_id: str, story_id: str, voice_id: str, speech_rate: float) -> Audio:
        story = await db.get(Story, story_id)
        if story is None:
            raise HTTPException(status_code=404, detail="故事不存在")

        project = await db.get(Project, story.project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="项目不存在")
        if project.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权限访问此故事")

        ref_audio, ref_text = await self._get_voice_sample_data(db, voice_id, user_id)

        story_content = story.content

        audio = Audio(
            audio_id=str(uuid.uuid4()),
            story_id=story.story_id,
            title=story.title,
            user_id=user_id,
            file_url=None,
            speech_rate=str(speech_rate),
            status=0,
        )
        db.add(audio)
        await db.commit()
        await db.refresh(audio)

        asyncio.create_task(self._process_audio_job(audio.audio_id, story_content, ref_audio, ref_text))
        return audio

    async def get_audio_by_id(self, db: AsyncSession, audio_id: str) -> Optional[Audio]:
        return await db.get(Audio, audio_id)

    async def list_audios(self, db: AsyncSession, story_id: str, page: int, page_size: int, title: Optional[str] = None) -> tuple[list[Audio], int]:
        query = select(Audio).where(Audio.story_id == story_id)
        if title:
            query = query.where(Audio.title.contains(title))
        total = len((await db.execute(query)).scalars().all())
        rows = (await db.execute(query.order_by(Audio.create_time.desc()).offset((page - 1) * page_size).limit(page_size))).scalars().all()
        return rows, total

    async def update_audio_title(self, db: AsyncSession, audio_id: str, title: str) -> Optional[Audio]:
        audio = await db.get(Audio, audio_id)
        if audio is None:
            return None
        audio.title = title
        await db.commit()
        await db.refresh(audio)
        return audio

    async def delete_audio(self, db: AsyncSession, audio_id: str) -> bool:
        audio = await db.get(Audio, audio_id)
        if audio is None:
            return False
        await db.delete(audio)
        await db.commit()
        return True


audio_service = AudioService()
