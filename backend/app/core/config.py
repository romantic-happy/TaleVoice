"""
应用配置模块

使用pydantic-settings管理应用配置，从.env文件读取所有配置
"""

from pathlib import Path
from typing import Optional
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""
    APP_NAME: str = "TaleVoice"
    DEBUG: bool = True

    # 1. 去掉默认值 ""，强制从 .env 读取。若未配置，程序启动时会直接报错阻止运行
    DATABASE_URL: str

    # 2. 敏感信息使用 SecretStr，防止在日志打印 settings 时泄露
    SECRET_KEY: SecretStr
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    # OSS配置 (必填项去掉默认值)
    OSS_ACCESS_KEY_ID: str
    OSS_ACCESS_KEY_SECRET: SecretStr
    OSS_BUCKET_NAME: str
    OSS_ENDPOINT: str

    # 3. 明确可选配置
    OSS_CDN_DOMAIN: Optional[str] = None

    # 4. Pydantic V2 规范写法，替代原来的 class Config
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / ".env",
        env_file_encoding='utf-8',
        case_sensitive=True,
        # 建议加上这个：如果 .env 里有一些这里没定义的冗余变量，忽略它们而不是报错
        extra='ignore'
    )

# 告诉 PyCharm 忽略缺少参数的警告
# noinspection PyArgumentList
settings = Settings()  # type: ignore
