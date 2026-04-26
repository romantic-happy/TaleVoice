from pathlib import Path
from typing import Optional
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """应用配置类"""
    
    APP_NAME: str = "TaleVoice"
    DEBUG: bool = True

    # 数据库
    DATABASE_URL: str

    # 安全
    SECRET_KEY: SecretStr
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    # OSS配置 (合并：使用 gyx 的类型约束)
    OSS_ACCESS_KEY_ID: str
    OSS_ACCESS_KEY_SECRET: SecretStr
    OSS_BUCKET_NAME: str
    OSS_ENDPOINT: str
    OSS_CDN_DOMAIN: Optional[str] = None

    # OpenAI配置 (来自 gyx)
    OPENAI_API_KEY: SecretStr
    OPENAI_BASE_URL: Optional[str] = None

    # Qwen TTS配置 (合并：从 develop 迁入)
    TTS_MODEL_NAME: str = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
    TTS_DEVICE: str = "cpu"
    TTS_LANGUAGE: str = "Chinese"
    TTS_ATTENTION_IMPLEMENTATION: str = "eager"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / ".env",
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore'
    )

# noinspection PyArgumentList
settings = Settings()  # type: ignore