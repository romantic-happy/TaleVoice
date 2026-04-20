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

    class Config:
        env_file = Path(__file__).parent.parent.parent / ".env"
        case_sensitive = True


settings = Settings()
