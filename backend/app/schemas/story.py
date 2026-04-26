"""
故事导入模块数据模型

定义故事导入相关的请求和响应数据结构
"""

from pydantic import BaseModel, Field
from typing import Optional


class StoryCreate(BaseModel):
    """
    创建故事内容请求模型
    """
    title: str = Field(..., description="章节标题")
    content: str = Field(..., description="章节内容")


class StoryUpdate(BaseModel):
    """
    编辑故事内容请求模型
    """
    projectId: str = Field(..., description="项目ID")
    title: Optional[str] = Field(None, description="章节标题")
    content: Optional[str] = Field(None, description="章节内容")


class StoryAIRequest(BaseModel):
    """
    AI故事生成请求模型
    """
    theme: str = Field(..., description="主题")
    style: Optional[str] = Field(None, description="风格")
    keyword: Optional[str] = Field(None, description="关键词")
    prompt: Optional[str] = Field(None, description="要求")
    number: Optional[str] = Field(None, description="章节数量")
    length: Optional[str] = Field(None, description="每章长度")


class StoryAIUpdate(BaseModel):
    """
    AI故事内容修改请求模型
    """
    projectId: str = Field(..., description="项目ID")
    theme: Optional[str] = Field(None, description="主题")
    style: Optional[str] = Field(None, description="风格")
    keyword: Optional[str] = Field(None, description="关键词")
    prompt: str = Field(..., description="要求")
    number: Optional[str] = Field(None, description="章节数量")
    length: Optional[str] = Field(None, description="长度")
    rewrite: bool = Field(..., description="是否重写")