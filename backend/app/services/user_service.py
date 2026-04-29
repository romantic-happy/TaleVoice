"""
用户服务层

处理用户相关的业务逻辑，包括用户注册、登录、资料管理、密码修改等
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User
from app.core.security import create_access_token


class UserService:
    """用户服务类，提供用户相关的业务逻辑处理"""

    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """
        根据用户名查询用户

        Args:
            db: 数据库会话
            username: 用户名

        Returns:
            Optional[User]: 找到返回User对象，否则返回None
        """
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """
        根据邮箱查询用户

        Args:
            db: 数据库会话
            email: 邮箱地址

        Returns:
            Optional[User]: 找到返回User对象，否则返回None
        """
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        """
        根据用户ID查询用户

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            Optional[User]: 找到返回User对象，否则返回None
        """
        result = await db.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(db: AsyncSession, username: str, password: str, email: str) -> User:
        """
        创建新用户

        Args:
            db: 数据库会话
            username: 用户名
            password: 明文密码（直接存储）
            email: 邮箱地址

        Returns:
            User: 创建的用户对象
        """
        user = User(username=username, password=password, email=email)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
        """
        用户认证

        Args:
            db: 数据库会话
            username: 用户名
            password: 明文密码

        Returns:
            Optional[User]: 认证成功返回User对象，失败返回None
        """
        user = await UserService.get_user_by_username(db, username)
        if not user:
            return None
        if password != user.password:
            return None
        return user

    @staticmethod
    def create_token(user: User) -> str:
        """
        为用户创建JWT令牌

        Args:
            user: 用户对象

        Returns:
            str: JWT令牌字符串
        """
        token_data = {"sub": user.user_id, "username": user.username}
        return create_access_token(token_data)

    @staticmethod
    async def update_user_profile(
        db: AsyncSession, user_id: str, username: Optional[str] = None,
        email: Optional[str] = None, avatar: Optional[str] = None
    ) -> Optional[User]:
        """
        更新用户资料

        Args:
            db: 数据库会话
            user_id: 用户ID
            username: 新用户名（可选）
            email: 新邮箱（可选）
            avatar: 新头像URL（可选）

        Returns:
            Optional[User]: 更新成功返回用户对象，失败（用户名或邮箱已被使用）返回None
        """
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            return None
        if username is not None:
            existing = await UserService.get_user_by_username(db, username)
            if existing and existing.user_id != user_id:
                return None
            user.username = username
        if email is not None:
            existing = await UserService.get_user_by_email(db, email)
            if existing and existing.user_id != user_id:
                return None
            user.email = email
        if avatar is not None:
            user.avatar = avatar
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def update_password(db: AsyncSession, user_id: str, old_password: str, new_password: str) -> bool:
        """
        修改密码

        Args:
            db: 数据库会话
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码（直接存储）

        Returns:
            bool: 修改成功返回True，失败（用户不存在或旧密码错误）返回False
        """
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            return False
        if old_password != user.password:
            return False
        user.password = new_password
        await db.commit()
        return True


user_service = UserService()
