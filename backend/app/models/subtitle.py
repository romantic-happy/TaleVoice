"""
字幕和剪辑数据模型

定义字幕表、字幕片段表、剪辑任务表、剪辑片段表结构
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, BigInteger, Float, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class Subtitle(Base):
    """
    字幕模型类

    对应数据库中的t_subtitle表，存储视频字幕生成任务和结果信息
    """
    __tablename__ = "t_subtitle"

    subtitle_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(String(64), ForeignKey("t_video.video_id"), nullable=False, index=True)
    user_id = Column(String(64), ForeignKey("t_user.user_id"), nullable=False, index=True)
    title = Column(String(256), nullable=True)
    language = Column(String(16), default="zh-CN", nullable=False)
    format = Column(String(10), default="srt", nullable=False)
    content = Column(Text, nullable=True)
    file_url = Column(String(512), nullable=True)
    task_id = Column(String(128), nullable=True)
    status = Column(String(20), default="pending", nullable=False)
    confidence = Column(Float, nullable=True)
    create_time = Column(DateTime, default=datetime.now, nullable=False)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    video = relationship("Video", backref="subtitles")
    user = relationship("User", backref="subtitles")
    segments = relationship("SubtitleSegment", back_populates="subtitle", cascade="all, delete-orphan")


class SubtitleSegment(Base):
    """
    字幕片段模型类

    对应数据库中的t_subtitle_segment表，存储字幕的具体时间片段和文本内容
    """
    __tablename__ = "t_subtitle_segment"

    segment_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    subtitle_id = Column(String(64), ForeignKey("t_subtitle.subtitle_id", ondelete="CASCADE"), nullable=False, index=True)
    segment_index = Column(Integer, nullable=False)
    start_time = Column(BigInteger, nullable=False)
    end_time = Column(BigInteger, nullable=False)
    text = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    create_time = Column(DateTime, default=datetime.now, nullable=False)

    subtitle = relationship("Subtitle", back_populates="segments")


class EditTask(Base):
    """
    剪辑任务模型类

    对应数据库中的t_edit_task表，存储视频智能剪辑任务信息和结果
    """
    __tablename__ = "t_edit_task"

    task_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(64), ForeignKey("t_project.project_id"), nullable=False, index=True)
    user_id = Column(String(64), ForeignKey("t_user.user_id"), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    timeline_config = Column(JSON, nullable=True)
    output_url = Column(String(512), nullable=True)
    output_duration = Column(Integer, nullable=True)
    resolution = Column(String(20), default="1920x1080", nullable=False)
    fps = Column(Integer, default=30, nullable=False)
    aliyun_task_id = Column(String(128), nullable=True)
    status = Column(String(20), default="pending", nullable=False)
    progress = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    create_time = Column(DateTime, default=datetime.now, nullable=False)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    project = relationship("Project", backref="edit_tasks")
    user = relationship("User", backref="edit_tasks")
    clips = relationship("EditClip", back_populates="edit_task", cascade="all, delete-orphan")


class EditClip(Base):
    """
    剪辑片段模型类

    对应数据库中的t_edit_clip表，存储剪辑任务中各视频片段的详细配置
    """
    __tablename__ = "t_edit_clip"

    clip_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(64), ForeignKey("t_edit_task.task_id", ondelete="CASCADE"), nullable=False, index=True)
    video_id = Column(String(64), ForeignKey("t_video.video_id", ondelete="SET NULL"), nullable=True, index=True)
    video_url = Column(String(512), nullable=False)
    clip_order = Column(Integer, nullable=False)
    start_time = Column(Float, default=0, nullable=False)
    end_time = Column(Float, default=0, nullable=False)
    duration = Column(Float, default=0, nullable=False)
    transition_in = Column(String(32), default="fade", nullable=False)
    transition_out = Column(String(32), default="fade", nullable=False)
    transition_duration = Column(Float, default=0.5, nullable=False)
    filter_type = Column(String(32), default="none", nullable=False)
    volume = Column(Integer, default=100, nullable=False)
    create_time = Column(DateTime, default=datetime.now, nullable=False)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    edit_task = relationship("EditTask", back_populates="clips")
    video = relationship("Video", backref="edit_clips")
