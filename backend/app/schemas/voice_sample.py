"""
音色样本相关的数据Schema

定义音色样本创建、更新、查询等接口的请求和响应数据结构
"""

from typing import Optional, List

from pydantic import BaseModel


class VoiceSampleCreate(BaseModel):
    """音色样本创建请求Schema"""
    voiceName: Optional[str] = None


class VoiceSampleUpdate(BaseModel):
    """音色样本更新请求Schema"""
    voiceId: str
    voiceName: str


class VoiceSampleResponse(BaseModel):
    """音色样本响应Schema"""
    voiceId: str
    voiceName: str
    default: bool

    class Config:
        from_attributes = True


class VoiceSampleListResponse(BaseModel):
    """音色样本列表响应Schema"""
    code: int
    message: str
    data: List[VoiceSampleResponse]
