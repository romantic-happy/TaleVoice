from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List, Dict, Any
from app.models.video import BGM
import uuid
from datetime import datetime


class BGMProcessor:
    async def list_bgm(
        self,
        db: AsyncSession,
        style: Optional[str] = None,
        emotion: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        stmt = select(BGM)
        
        if style:
            stmt = stmt.where(BGM.style == style)
        if emotion:
            stmt = stmt.where(BGM.emotion == emotion)
        
        result = await db.execute(stmt)
        bgms = result.scalars().all()
        
        return [self._bgm_to_dict(b) for b in bgms]

    async def get_bgm_by_id(self, db: AsyncSession, bgm_id: str) -> Optional[Dict[str, Any]]:
        stmt = select(BGM).where(BGM.bgm_id == bgm_id)
        result = await db.execute(stmt)
        bgm = result.scalar_one_or_none()
        
        if bgm:
            return self._bgm_to_dict(bgm)
        return None

    async def recommend_bgm(self, db: AsyncSession, story_content: str) -> List[Dict[str, Any]]:
        emotion = await self._analyze_emotion(story_content)
        style = await self._detect_style(story_content)
        
        stmt = select(BGM)
        if emotion:
            stmt = stmt.where(BGM.emotion == emotion)
        if style:
            stmt = stmt.where(BGM.style == style)
        
        result = await db.execute(stmt.limit(5))
        bgms = result.scalars().all()
        
        return [self._bgm_to_dict(b) for b in bgms]

    async def _analyze_emotion(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        
        if any(w in text_lower for w in ["快乐", "幸福", "开心", "高兴"]):
            return "happy"
        if any(w in text_lower for w in ["悲伤", "难过", "痛苦"]):
            return "sad"
        if any(w in text_lower for w in ["紧张", "刺激", "冒险"]):
            return "exciting"
        if any(w in text_lower for w in ["温暖", "温馨", "爱"]):
            return "warm"
        
        return None

    async def _detect_style(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        
        if any(w in text_lower for w in ["童话", "魔法", "奇幻"]):
            return "fantasy"
        if any(w in text_lower for w in ["冒险", "旅行", "探索"]):
            return "adventure"
        if any(w in text_lower for w in ["日常", "生活", "家庭"]):
            return "daily"
        
        return None

    def _bgm_to_dict(self, bgm: BGM) -> Dict[str, Any]:
        return {
            "bgm_id": bgm.bgm_id,
            "name": bgm.name,
            "style": bgm.style,
            "emotion": bgm.emotion,
            "duration": bgm.duration,
            "file_url": bgm.file_url,
            "sample_url": bgm.sample_url
        }


bgm_processor = BGMProcessor()
