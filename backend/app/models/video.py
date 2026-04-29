from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime


class Video(Base):
    __tablename__ = "t_video"

    video_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("t_project.project_id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("t_user.user_id"), nullable=False)
    source_image_url = Column(String(512))
    file_url = Column(String(512))
    prompt = Column(Text)
    duration = Column(Integer, default=4)
    resolution = Column(String(20), default="720p")
    fps = Column(Integer, default=24)
    file_size = Column(Integer)
    format = Column(String(20), default="mp4")
    status = Column(String(20), default="pending")
    task_id = Column(String(128))
    error_message = Column(Text)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Video {self.video_id}>"


class BGM(Base):
    __tablename__ = "t_bgm"

    bgm_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(256), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("t_user.user_id"))
    source = Column(String(32), default="system")
    style = Column(String(128))
    emotion = Column(String(64))
    file_url = Column(String(512))
    sample_url = Column(String(512))
    duration = Column(Integer)
    bpm = Column(Integer)
    format = Column(String(32), default="mp3")
    sample_rate = Column(Integer)
    channels = Column(Integer)
    bit_rate = Column(Integer)
    file_size = Column(Integer)
    play_count = Column(Integer, default=0)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<BGM {self.name}>"
