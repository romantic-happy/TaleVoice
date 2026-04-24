"""
应用配置模块

使用pydantic-settings管理应用配置，从.env文件读取所有配置
"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    APP_NAME: str = "TaleVoice"
    DEBUG: bool = True

    DATABASE_URL: str = ""

    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    # OSS配置
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_BUCKET_NAME: str = ""
    OSS_ENDPOINT: str = ""
    OSS_CDN_DOMAIN: str = ""

    # AI视频生成配置
    AI_PROVIDER: str = "mock"

    # 阿里云通义万相视频生成API配置
    ALIYUN_ACCESS_KEY_ID: str = ""
    ALIYUN_ACCESS_KEY_SECRET: str = ""
    ALIYUN_VIDEO_API_KEY: str = ""
    ALIYUN_VIDEO_ENDPOINT: str = "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation"
    ALIYUN_VIDEO_MODEL: str = "wanx2.1-i2v-plus"

    # 阿里云通义千问大模型API配置（提示词工程）
    ALIYUN_LLM_API_KEY: str = ""
    ALIYUN_LLM_ENDPOINT: str = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    ALIYUN_LLM_MODEL: str = "qwen-max"

    # 阿里云语音合成API配置
    ALIYUN_TTS_APP_KEY: str = ""
    ALIYUN_TTS_ACCESS_KEY_ID: str = ""
    ALIYUN_TTS_ACCESS_KEY_SECRET: str = ""

    # 阿里云字幕生成API配置
    ALIYUN_SUBTITLE_APP_KEY: str = ""
    ALIYUN_SUBTITLE_CALLBACK_URL: str = ""

    # 阿里云智能剪辑API配置
    ALIYUN_EDIT_REGION: str = "cn-shanghai"
    ALIYUN_EDIT_CALLBACK_URL: str = ""
    ALIYUN_EDIT_OUTPUT_BUCKET: str = ""

    class Config:
        env_file = Path(__file__).parent.parent.parent / ".env"
        case_sensitive = True


settings = Settings()
