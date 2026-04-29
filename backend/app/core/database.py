"""
数据库连接模块

负责创建数据库引擎和会话管理，提供依赖注入函数获取数据库会话
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
AsyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

Base = declarative_base()


async def get_db():
    """
    数据库会话依赖注入函数

    用于FastAPI的Depends()，自动管理数据库连接的创建和关闭
    Yields:
        AsyncSession: 异步数据库会话对象
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
