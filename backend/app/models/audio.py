"""
故事章节和语音数据模型

定义故事章节表、语音表和语音-音色关联表结构
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


class Story(Base):
    """
    故事章节模型类

    对应数据库中的t_story表，存储故事章节的标题、内容和摘要
    """
    __tablename__ = "t_story"

    story_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(256), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    chapter_number = Column(Integer, nullable=False)
    project_id = Column(String(64), ForeignKey("t_project.project_id"), nullable=False, index=True)
    create_time = Column(DateTime, default=datetime.now, nullable=False)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    project = relationship("Project", back_populates="stories")
    audios = relationship("Audio", back_populates="story")


class Audio(Base):
    """
    语音模型类

    对应数据库中的t_audio表，存储生成的语音文件信息
    """
    __tablename__ = "t_audio"

    audio_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    story_id = Column(String(64), ForeignKey("t_story.story_id"), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    user_id = Column(String(64), ForeignKey("t_user.user_id"), nullable=False, index=True)
    file_url = Column(String(512), nullable=True)
    speech_rate = Column(String(10), default="1.00", nullable=False)
    status = Column(Integer, default=0, nullable=False)
    create_time = Column(DateTime, default=datetime.now, nullable=False)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    story = relationship("Story", back_populates="audios")
    user = relationship("User", back_populates="audios")
    audio_voice_rels = relationship("AudioVoiceRel", back_populates="audio")


class AudioVoiceRel(Base):
    """
    语音-音色关联模型类

    对应数据库中的t_audio_voice_rel表，记录语音使用的音色
    """
    __tablename__ = "t_audio_voice_rel"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    audio_id = Column(String(64), ForeignKey("t_audio.audio_id"), nullable=False, index=True)
    voice_id = Column(String(64), ForeignKey("t_voice_sample.voice_id"), nullable=False, index=True)
    create_time = Column(DateTime, default=datetime.now, nullable=False)

    audio = relationship("Audio", back_populates="audio_voice_rels")
