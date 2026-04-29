"""
音色样本数据模型

定义克隆音频样本表结构，用于存储用户上传的参考音频信息
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


class VoiceSample(Base):
    """
    音色样本模型类

    对应数据库中的t_voice_sample表，存储用户克隆的音色样本信息
    """
    __tablename__ = "t_voice_sample"

    voice_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    voice_name = Column(String(128), nullable=False)
    user_id = Column(String(64), ForeignKey("t_user.user_id"), nullable=False, index=True)
    audio_url = Column(String(512), nullable=True)
    is_default = Column(Integer, default=0, nullable=False)
    create_time = Column(DateTime, default=datetime.now, nullable=False)

    user = relationship("User", back_populates="voice_samples")
