"""
安全认证模块

提供JWT令牌创建与验证、密码哈希处理、请求拦截器等功能
"""

from datetime import datetime, timedelta
from typing import Optional
import hashlib
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.core.config import settings

security = HTTPBearer()


def get_password_hash(password: str) -> str:
    """
    对密码进行哈希处理

    Args:
        password: 明文密码

    Returns:
        str: 哈希后的密码
    """
    # 使用 SHA-256 进行密码哈希（实际生产环境建议使用 bcrypt）
    salt = os.urandom(16).hex()
    hash_obj = hashlib.sha256((password + salt).encode())
    return f"{salt}:{hash_obj.hexdigest()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码与哈希密码是否匹配

    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码

    Returns:
        bool: 密码是否匹配
    """
    try:
        salt, hash_value = hashed_password.split(":")
        hash_obj = hashlib.sha256((plain_password + salt).encode())
        return hash_obj.hexdigest() == hash_value
    except:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌

    Args:
        data: 需要编码到令牌中的数据，包含sub(user_id)和username
        expires_delta: 令牌过期时间增量，默认为配置中的过期时间

    Returns:
        str: 编码后的JWT令牌字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    解码并验证JWT令牌

    Args:
        token: JWT令牌字符串

    Returns:
        Optional[dict]: 解码后的payload，验证失败返回None
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    获取当前认证用户（强制认证）

    用于需要用户必须登录才能访问的接口
    如果令牌无效或过期，抛出401未授权异常

    Args:
        credentials: HTTP Bearer认证凭证

    Returns:
        dict: 包含user_id和username的用户信息字典

    Raises:
        HTTPException: 令牌无效时抛出401异常
    """
    token = credentials.credentials
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"user_id": user_id, "username": payload.get("username")}


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """
    获取当前认证用户（可选认证）

    用于用户登录或注册等不需要强制认证的接口
    如果没有令牌或令牌无效，返回None而不是抛出异常

    Args:
        credentials: HTTP Bearer认证凭证，可为None

    Returns:
        Optional[dict]: 包含user_id和username的用户信息字典，无令牌时返回None
    """
    if credentials is None:
        return None
    token = credentials.credentials
    payload = decode_token(token)
    if payload is None:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    return {"user_id": user_id, "username": payload.get("username")}
