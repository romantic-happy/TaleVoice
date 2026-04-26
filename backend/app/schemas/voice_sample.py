"""
音色样本相关的数据Schema

定义音色样本创建、更新、查询等接口的请求和响应数据结构
"""

from typing import Optional, List

from pydantic import BaseModel, Field


class VoiceSampleCreate(BaseModel):
    """音色样本创建请求Schema"""
    voiceName: Optional[str] = None


class VoiceSampleUpdate(BaseModel):
    """音色样本更新请求Schema"""
    voiceId: str
    voiceName: str


class VoiceSampleResponse(BaseModel):
    voiceId: str = Field(
        validation_alias="voice_id",
        serialization_alias="voiceId",
    )
    voiceName: str = Field(
        validation_alias="voice_name",
        serialization_alias="voiceName",
    )
    default: bool = Field(
        validation_alias="is_default",
        serialization_alias="default",
    ) # 映射数据库的 is_default

    class Config:
        from_attributes = True
        populate_by_name = True # 允许通过字段名或校验别名赋值


class VoiceSampleListResponse(BaseModel):
    """音色样本列表响应Schema"""
    code: int
    message: str
    data: List[VoiceSampleResponse]
