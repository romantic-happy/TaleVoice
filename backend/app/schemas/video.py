"""
视频相关的数据Schema

定义视频生成、背景音乐配置等接口的请求和响应数据结构
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field


class VideoStatus(int, Enum):
    """视频状态枚举"""
    PENDING = 0
    PROCESSING = 1
    COMPLETED = 2
    FAILED = 3


class BGMSource(str, Enum):
    """背景音乐来源枚举"""
    SYSTEM = "system"
    USER = "user"


class BGMSyncMode(str, Enum):
    """背景音乐同步模式枚举"""
    AUTO = "auto"
    MANUAL = "manual"


class VideoCreate(BaseModel):
    """视频生成请求Schema"""
    project_id: str = Field(..., description="项目ID")
    title: str = Field(..., min_length=1, max_length=200, description="视频标题")
    description: Optional[str] = Field(None, description="视频描述")
    source_image_url: str = Field(..., description="源图片URL")
    prompt: Optional[str] = Field(None, description="自定义提示词，不填则根据故事文本自动生成")
    bgm_id: Optional[str] = Field(None, description="背景音乐ID")
    bgm_volume: int = Field(default=30, ge=0, le=100, description="背景音乐音量百分比(0-100)")
    bgm_fade_in: float = Field(default=1.0, ge=0.0, le=5.0, description="淡入时长(秒)")
    bgm_fade_out: float = Field(default=1.5, ge=0.0, le=5.0, description="淡出时长(秒)")
    bgm_loop: bool = Field(default=True, description="是否循环播放")


class VideoUpdate(BaseModel):
    """视频更新请求Schema"""
    video_id: str = Field(..., description="视频ID")
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="视频标题")
    description: Optional[str] = Field(None, description="视频描述")


class VideoBGMConfig(BaseModel):
    """视频背景音乐配置请求Schema"""
    bgm_id: str = Field(..., description="背景音乐ID")
    volume: int = Field(default=30, ge=0, le=100, description="音量百分比(0-100)")
    fade_in: float = Field(default=1.0, ge=0.0, le=5.0, description="淡入时长(秒)")
    fade_out: float = Field(default=1.5, ge=0.0, le=5.0, description="淡出时长(秒)")
    loop: bool = Field(default=True, description="是否循环播放")
    start_offset: float = Field(default=0.0, ge=0.0, description="起始偏移(秒)")
    sync_mode: BGMSyncMode = Field(default=BGMSyncMode.AUTO, description="同步模式")


class VideoResponse(BaseModel):
    """视频响应Schema"""
    video_id: str
    project_id: str
    user_id: str
    title: str
    description: Optional[str] = None
    source_image_url: Optional[str] = None
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None
    resolution: Optional[str] = None
    fps: Optional[int] = None
    file_size: Optional[int] = None
    format: str = "mp4"
    status: int = 0
    status_text: str = "pending"
    prompt: Optional[str] = None
    bgm_id: Optional[str] = None
    bgm_volume: int = 30
    bgm_fade_in: str = "1.0"
    bgm_fade_out: str = "1.5"
    bgm_loop: int = 1
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class VideoListItem(BaseModel):
    """视频列表项Schema"""
    video_id: str
    project_id: str
    title: str
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None
    status: int = 0
    status_text: str = "pending"
    create_time: Optional[datetime] = None


class VideoListData(BaseModel):
    """视频列表数据Schema"""
    total: int
    lists: List[VideoListItem]


class VideoListResponse(BaseModel):
    """视频列表响应Schema"""
    code: int
    message: str
    data: VideoListData


class BGMUploadRequest(BaseModel):
    """背景音乐上传请求Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="音乐名称")
    style: Optional[str] = Field(None, description="音乐风格标签")
    emotion: Optional[str] = Field(None, description="情感标签")


class BGMResponse(BaseModel):
    """背景音乐响应Schema"""
    bgm_id: str
    name: str
    source: str = "system"
    style: Optional[str] = None
    emotion: Optional[str] = None
    file_url: Optional[str] = None
    sample_url: Optional[str] = None
    duration: Optional[int] = None
    bpm: Optional[int] = None
    format: str = "mp3"
    play_count: int = 0

    class Config:
        from_attributes = True


class BGMListItem(BaseModel):
    """背景音乐列表项Schema"""
    bgm_id: str
    name: str
    source: str
    style: Optional[str] = None
    emotion: Optional[str] = None
    duration: Optional[int] = None
    sample_url: Optional[str] = None
    bpm: Optional[int] = None


class BGMListData(BaseModel):
    """背景音乐列表数据Schema"""
    total: int
    lists: List[BGMListItem]


class BGMListResponse(BaseModel):
    """背景音乐列表响应Schema"""
    code: int
    message: str
    data: BGMListData


class BGMRecommendResponse(BaseModel):
    """背景音乐推荐响应Schema"""
    code: int
    message: str
    data: BGMListData


class VideoErrorCode:
    """视频模块错误码常量定义"""
    VIDEO_NOT_FOUND = 4001
    VIDEO_NO_PERMISSION = 4002
    VIDEO_GENERATION_FAILED = 4003
    VIDEO_ALREADY_PROCESSING = 4004
    BGM_NOT_FOUND = 6005
    BGM_INVALID_FORMAT = 6001
    BGM_FILE_TOO_LARGE = 6002
    BGM_DURATION_INVALID = 6003
    BGM_FILE_CORRUPTED = 6004
    BGM_VOLUME_INVALID = 6006
    AI_SERVICE_UNAVAILABLE = 5001
    AI_SERVICE_TIMEOUT = 5002
