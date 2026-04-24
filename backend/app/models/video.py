"""
视频数据模型

定义视频表和背景音乐表结构，用于存储AI生成的视频信息和背景音乐配置
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, BigInteger
from sqlalchemy.orm import relationship

from app.core.database import Base


class Video(Base):
    """
    视频模型类

    对应数据库中的t_video表，存储由图片通过AI大模型生成的视频信息
    与项目表(t_project)关联，一个项目可拥有多个视频
    """
    __tablename__ = "t_video"

    video_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(64), ForeignKey("t_project.project_id"), nullable=False, index=True)
    user_id = Column(String(64), ForeignKey("t_user.user_id"), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    source_image_url = Column(String(512), nullable=True)
    file_url = Column(String(512), nullable=True)
    thumbnail_url = Column(String(512), nullable=True)
    duration = Column(Integer, nullable=True)
    resolution = Column(String(32), nullable=True)
    fps = Column(Integer, nullable=True)
    file_size = Column(BigInteger, nullable=True)
    format = Column(String(32), default="mp4", nullable=False)
    status = Column(Integer, default=0, nullable=False)
    prompt = Column(Text, nullable=True)
    bgm_id = Column(String(64), ForeignKey("t_bgm.bgm_id"), nullable=True)
    bgm_volume = Column(Integer, default=30, nullable=False)
    bgm_fade_in = Column(String(16), default="1.0", nullable=False)
    bgm_fade_out = Column(String(16), default="1.5", nullable=False)
    bgm_loop = Column(Integer, default=1, nullable=False)
    create_time = Column(DateTime, default=datetime.now, nullable=False)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    project = relationship("Project", backref="videos")
    user = relationship("User", backref="videos")
    bgm = relationship("BGM", backref="videos")


class BGM(Base):
    """
    背景音乐模型类

    对应数据库中的t_bgm表，存储系统预置和用户上传的背景音乐信息
    """
    __tablename__ = "t_bgm"

    bgm_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(256), nullable=False)
    user_id = Column(String(64), ForeignKey("t_user.user_id"), nullable=True, index=True)
    source = Column(String(32), default="system", nullable=False)
    style = Column(String(128), nullable=True)
    emotion = Column(String(64), nullable=True)
    file_url = Column(String(512), nullable=True)
    sample_url = Column(String(512), nullable=True)
    duration = Column(Integer, nullable=True)
    bpm = Column(Integer, nullable=True)
    format = Column(String(32), default="mp3", nullable=False)
    sample_rate = Column(Integer, nullable=True)
    channels = Column(Integer, nullable=True)
    bit_rate = Column(Integer, nullable=True)
    file_size = Column(BigInteger, nullable=True)
    play_count = Column(Integer, default=0, nullable=False)
    create_time = Column(DateTime, default=datetime.now, nullable=False)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    user = relationship("User", backref="bgms")
