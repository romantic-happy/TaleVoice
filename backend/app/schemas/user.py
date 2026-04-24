"""
用户相关的数据Schema

定义用户注册、登录、资料更新等接口的请求和响应数据结构
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    """用户注册请求Schema"""
    username: str
    password: str
    email: EmailStr


class UserLogin(BaseModel):
    """用户登录请求Schema"""
    username: str
    password: str


class UserProfile(BaseModel):
    """用户个人信息响应Schema"""
    userId: str
    username: str
    email: str
    avatar: Optional[str] = None
    createTime: datetime

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """用户资料更新请求Schema"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar: Optional[str] = None


class PasswordChange(BaseModel):
    """密码修改请求Schema"""
    oldPassword: str
    newPassword: str


class PasswordReset(BaseModel):
    """密码重置请求Schema"""
    email: EmailStr


class TokenResponse(BaseModel):
    """Token响应Schema"""
    code: int
    message: str
    data: str


class CommonResponse(BaseModel):
    """通用响应Schema"""
    code: int
    message: str
    data: Optional[dict] = None
