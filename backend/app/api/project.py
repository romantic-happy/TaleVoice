"""
项目模块API路由

提供项目的创建、修改、删除、查询等接口
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logger import app_logger
from app.schemas.common import ResponseModel, APIException, ErrorCode
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectListData,
    ProjectListResponse,
)
from app.services.project_service import project_service

router = APIRouter(prefix="/api/project", tags=["项目模块"])


@router.post("", response_model=ResponseModel)
async def create_project(
    project_data: ProjectCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建项目接口

    - 需要JWT认证
    - 创建一个新的项目
    - 返回项目ID
    """
    app_logger.info(f"创建项目请求: {current_user.get('username')}, 标题: {project_data.title}")

    project = await project_service.create_project(
        db,
        current_user["user_id"],
        project_data.title,
        project_data.description,
        project_data.style
    )

    app_logger.info(f"创建项目成功: {project.project_id}")
    return ResponseModel(code=200, message="创建成功", data=project.project_id)


@router.put("", response_model=ResponseModel)
async def update_project(
    project_data: ProjectUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    修改项目接口

    - 需要JWT认证
    - 只能修改属于自己的项目
    """
    app_logger.info(f"更新项目请求: {current_user.get('username')}, ID: {project_data.projectId}")

    project = await project_service.get_project_by_id(db, project_data.projectId)
    if not project:
        app_logger.error(f"更新项目失败-不存在: {project_data.projectId}")
        raise APIException(code=ErrorCode.NOT_FOUND, message="项目不存在")

    if project.user_id != current_user["user_id"]:
        app_logger.warning(f"更新项目失败-无权限: {current_user.get('username')}, ID: {project_data.projectId}")
        raise APIException(code=ErrorCode.FORBIDDEN, message="无权限修改此项目")

    updated_project = await project_service.update_project(
        db,
        project_data.projectId,
        project_data.title,
        project_data.description,
        project_data.style
    )

    app_logger.info(f"更新项目成功: {project_data.projectId}")
    return ResponseModel(code=200, message="修改成功", data=None)


@router.delete("/{project_id}", response_model=ResponseModel)
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除项目接口

    - 需要JWT认证
    - 只能删除属于自己的项目
    """
    app_logger.info(f"删除项目请求: {current_user.get('username')}, ID: {project_id}")

    project = await project_service.get_project_by_id(db, project_id)
    if not project:
        app_logger.error(f"删除项目失败-不存在: {project_id}")
        raise APIException(code=ErrorCode.NOT_FOUND, message="项目不存在")

    if project.user_id != current_user["user_id"]:
        app_logger.warning(f"删除项目失败-无权限: {current_user.get('username')}, ID: {project_id}")
        raise APIException(code=ErrorCode.FORBIDDEN, message="无权限删除此项目")

    await project_service.delete_project(db, project_id)
    app_logger.info(f"删除项目成功: {project_id}")
    return ResponseModel(code=200, message="删除成功", data=None)


@router.get("/list", response_model=ProjectListResponse)
async def get_project_list(
    page: int = Query(1, ge=1, description="第几页"),
    pageSize: int = Query(10, ge=1, le=100, description="每页多少条"),
    title: Optional[str] = Query(None, description="搜索关键词，支持部分匹配"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取项目列表接口

    - 需要JWT认证
    - 返回当前用户的项目列表（分页）
    """
    app_logger.info(f"获取项目列表: {current_user.get('username')}, 页码: {page}, 每页: {pageSize}")

    projects, total = await project_service.get_projects_by_user(
        db,
        current_user["user_id"],
        page,
        pageSize,
        title
    )

    lists = [
        {
            "projectId": p.project_id,
            "title": p.title,
            "description": p.description,
            "style": p.style
        }
        for p in projects
    ]

    app_logger.info(f"获取项目列表成功: {current_user.get('username')}, 总数: {total}")
    return ProjectListResponse(
        code=200,
        message="获取成功",
        date=ProjectListData(total=total, lists=lists)
    )
