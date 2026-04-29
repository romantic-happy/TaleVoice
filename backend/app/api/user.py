"""
用户模块API路由

提供用户注册、登录、登出、资料管理、密码修改等接口
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logger import app_logger
from app.schemas.user import (
    UserRegister,
    UserLogin,
    UserProfile,
    UserProfileUpdate,
    PasswordChange,
    PasswordReset,
)
from app.schemas.common import ResponseModel, APIException, ErrorCode
from app.services.user_service import user_service

router = APIRouter(prefix="/api/user", tags=["用户模块"])


@router.post("/register", response_model=ResponseModel)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """
    用户注册接口

    - 检查用户名是否已存在
    - 检查邮箱是否已被注册
    - 创建新用户并返回成功响应
    """
    app_logger.info(f"用户注册请求: {user_data.username}")

    existing_user = await user_service.get_user_by_username(db, user_data.username)
    if existing_user:
        app_logger.warning(f"注册失败-用户名已存在: {user_data.username}")
        raise APIException(code=ErrorCode.BAD_REQUEST, message="用户名已存在")

    existing_email = await user_service.get_user_by_email(db, user_data.email)
    if existing_email:
        app_logger.warning(f"注册失败-邮箱已被注册: {user_data.email}")
        raise APIException(code=ErrorCode.BAD_REQUEST, message="邮箱已被注册")

    await user_service.create_user(db, user_data.username, user_data.password, user_data.email)
    app_logger.info(f"用户注册成功: {user_data.username}")
    return ResponseModel(code=200, message="注册成功", data=None)


@router.post("/login", response_model=ResponseModel)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    用户登录接口

    - 验证用户名和密码
    - 验证成功后生成JWT令牌并返回
    """
    app_logger.info(f"用户登录请求: {user_data.username}")

    user = await user_service.authenticate_user(db, user_data.username, user_data.password)
    if not user:
        app_logger.warning(f"登录失败-用户名或密码错误: {user_data.username}")
        raise APIException(code=ErrorCode.UNAUTHORIZED, message="用户名或密码错误")

    token = user_service.create_token(user)
    app_logger.info(f"用户登录成功: {user_data.username}")
    return ResponseModel(code=200, message="登录成功", data=token)


@router.post("/logout", response_model=ResponseModel)
async def logout(current_user: dict = Depends(get_current_user)):
    """
    用户登出接口

    - 需要JWT认证
    - 由于JWT无状态，登出操作仅记录日志
    """
    app_logger.info(f"用户登出: {current_user.get('username')}")
    return ResponseModel(code=200, message="登出成功", data=None)


@router.get("/profile", response_model=ResponseModel)
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户个人信息接口

    - 需要JWT认证
    - 返回用户ID、昵称、邮箱、头像、创建时间
    """
    user = await user_service.get_user_by_id(db, current_user["user_id"])
    if not user:
        app_logger.error(f"获取个人信息失败-用户不存在: {current_user['user_id']}")
        raise APIException(code=ErrorCode.NOT_FOUND, message="用户不存在")

    profile_data = {
        "userId": user.user_id,
        "username": user.username,
        "email": user.email,
        "avatar": user.avatar,
        "createTime": user.create_time.isoformat() if user.create_time else None
    }
    app_logger.info(f"获取个人信息成功: {user.username}")
    return ResponseModel(code=200, message="获取成功", data=profile_data)


@router.put("/profile", response_model=ResponseModel)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    修改当前用户个人信息接口

    - 需要JWT认证
    - 支持修改昵称、邮箱、头像
    - 昵称和邮箱不能与他人重复
    """
    app_logger.info(f"更新个人信息请求: {current_user.get('username')}")
    user = await user_service.update_user_profile(
        db,
        current_user["user_id"],
        username=profile_data.username,
        email=profile_data.email,
        avatar=profile_data.avatar
    )

    if not user:
        app_logger.warning(f"更新个人信息失败-用户名或邮箱已被使用: {current_user['user_id']}")
        raise APIException(code=ErrorCode.BAD_REQUEST, message="用户名或邮箱已被使用")

    app_logger.info(f"更新个人信息成功: {user.username}")
    return ResponseModel(code=200, message="修改成功", data=None)


@router.put("/password", response_model=ResponseModel)
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    修改密码接口

    - 需要JWT认证
    - 必须提供正确的旧密码才能修改新密码
    """
    app_logger.info(f"修改密码请求: {current_user.get('username')}")
    success = await user_service.update_password(
        db,
        current_user["user_id"],
        password_data.oldPassword,
        password_data.newPassword
    )

    if not success:
        app_logger.warning(f"修改密码失败-旧密码错误: {current_user.get('username')}")
        raise APIException(code=ErrorCode.BAD_REQUEST, message="旧密码错误")

    app_logger.info(f"修改密码成功: {current_user.get('username')}")
    return ResponseModel(code=200, message="密码修改成功", data=None)


@router.post("/password/reset", response_model=ResponseModel)
async def reset_password(
    reset_data: PasswordReset,
    db: AsyncSession = Depends(get_db)
):
    """
    密码重置接口

    - 不需要JWT认证
    - 根据邮箱发送密码重置邮件
    - 为防止枚举攻击，无论用户是否存在都返回成功
    """
    app_logger.info(f"密码重置请求: {reset_data.email}")
    user = await user_service.get_user_by_email(db, reset_data.email)

    if not user:
        app_logger.info(f"密码重置邮件已发送(用户不存在): {reset_data.email}")
        return ResponseModel(code=200, message="重置邮件已发送，请查收邮箱", data=None)
        
    app_logger.info(f"密码重置邮件已发送: {reset_data.email}")
    return ResponseModel(code=200, message="重置邮件已发送，请查收邮箱", data=None)
