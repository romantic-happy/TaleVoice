"""
应用配置模块

使用pydantic-settings管理应用配置，从.env文件读取所有配置
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / ".env",
        case_sensitive=True,
    )

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

    # Qwen TTS配置
    TTS_MODEL_NAME: str = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
    TTS_DEVICE: str = "cpu"
    TTS_LANGUAGE: str = "Chinese"
    TTS_ATTENTION_IMPLEMENTATION: str = "eager"



settings = Settings()
