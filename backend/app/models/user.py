"""
用户数据模型

定义用户表结构，包含用户基本信息、认证信息和关联关系
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """
    用户模型类

    对应数据库中的t_user表，存储用户基本信息
    """
    __tablename__ = "t_user"

    user_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(64), unique=True, nullable=False, index=True)
    password = Column(String(256), nullable=False)
    email = Column(String(128), unique=True, nullable=False, index=True)
    avatar = Column(String(512), nullable=True)
    create_time = Column(DateTime, default=datetime.now, nullable=False)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    voice_samples = relationship("VoiceSample", back_populates="user")
    projects = relationship("Project", back_populates="user")
    audios = relationship("Audio", back_populates="user")
