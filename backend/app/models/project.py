"""
项目数据模型

定义项目表结构，用于存储用户创建的故事项目信息
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Project(Base):
    """
    项目模型类

    对应数据库中的t_project表，存储用户创建的故事项目
    """
    __tablename__ = "t_project"

    project_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    style = Column(String(128), nullable=True)
    user_id = Column(String(64), ForeignKey("t_user.user_id"), nullable=False, index=True)
    create_time = Column(DateTime, default=datetime.now, nullable=False)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    user = relationship("User", back_populates="projects")
    stories = relationship("Story", back_populates="project")
