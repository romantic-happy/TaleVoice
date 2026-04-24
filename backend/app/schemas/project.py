"""
项目相关的数据Schema

定义项目创建、更新、查询等接口的请求和响应数据结构
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    """项目创建请求Schema"""
    title: str
    description: Optional[str] = None
    style: Optional[str] = None


class ProjectUpdate(BaseModel):
    """项目更新请求Schema"""
    projectId: str
    title: Optional[str] = None
    description: Optional[str] = None
    style: Optional[str] = None


class ProjectResponse(BaseModel):
    """项目响应Schema"""
    projectId: str
    title: str
    description: Optional[str] = None
    style: Optional[str] = None
    createTime: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectListItem(BaseModel):
    """项目列表项Schema"""
    projectId: str
    title: str
    description: Optional[str] = None
    style: Optional[str] = None


class ProjectListData(BaseModel):
    """项目列表数据Schema"""
    total: int
    lists: List[ProjectListItem]


class ProjectListResponse(BaseModel):
    """项目列表响应Schema"""
    code: int
    message: str
    data: ProjectListData
