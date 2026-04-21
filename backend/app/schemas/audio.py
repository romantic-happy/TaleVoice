"""
音频模块Schema

定义语音生成、查询和修改接口的请求与响应结构
"""

from typing import List

from pydantic import BaseModel, Field, ConfigDict


class AudioGenerateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    storyId: str = Field(..., description="故事章节ID")
    voiceId: str = Field(..., description="克隆音色ID")
    speechRate: float = Field(..., description="语速，0.5~2")


class AudioUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    audioId: str = Field(..., description="语音ID")
    title: str = Field(..., description="标题")


class AudioListItem(BaseModel):
    audioId: str
    title: str


class AudioListData(BaseModel):
    total: int
    lists: List[AudioListItem]


class AudioCreateData(BaseModel):
    audioId: str
    title: str
