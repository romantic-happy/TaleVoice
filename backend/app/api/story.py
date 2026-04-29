"""
故事导入模块API路由

提供故事内容的创建、编辑、删除、获取、导出以及AI故事生成等接口
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logger import app_logger
from app.schemas.story import (
    StoryCreate,
    StoryUpdate,
    StoryAIRequest,
    StoryAIUpdate
)
from app.schemas.common import ResponseModel, APIException, ErrorCode
from app.services.story_service import story_service

router = APIRouter(prefix="/api/story", tags=["故事导入模块"])


@router.get("/list/{projectId}", response_model=ResponseModel)
async def get_story_list(
    projectId: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取故事内容接口

    - 需要JWT认证
    - 根据项目ID获取故事内容
    """
    app_logger.info(f"获取故事内容请求: projectId={projectId}")
    
    story_data = await story_service.get_story_by_project_id(db, projectId, current_user["user_id"])
    if not story_data:
        app_logger.warning(f"获取故事内容失败-故事不存在: projectId={projectId}")
        raise APIException(code=ErrorCode.NOT_FOUND, message="故事不存在")
    
    app_logger.info(f"获取故事内容成功: projectId={projectId}")
    return ResponseModel(code=200, message="获取成功", data=story_data)


@router.post("", response_model=ResponseModel)
async def create_story(
    story_data: StoryCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建故事内容接口

    - 需要JWT认证
    - 创建新的故事内容
    """
    app_logger.info(f"创建故事内容请求: {story_data.title}")
    
    success = await story_service.create_story(db, story_data.title, story_data.content, current_user["user_id"])
    if not success:
        app_logger.warning(f"创建故事内容失败")
        raise APIException(code=ErrorCode.BAD_REQUEST, message="创建故事内容失败")
    
    app_logger.info(f"创建故事内容成功: {story_data.title}")
    return ResponseModel(code=200, message="创建成功", data=None)


@router.put("", response_model=ResponseModel)
async def update_story(
    story_data: StoryUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    编辑故事内容接口

    - 需要JWT认证
    - 根据项目ID更新故事内容
    """
    app_logger.info(f"编辑故事内容请求: projectId={story_data.projectId}")
    
    success = await story_service.update_story(
        db,
        story_data.projectId,
        story_data.title,
        story_data.content,
        current_user["user_id"]
    )
    if not success:
        app_logger.warning(f"编辑故事内容失败: projectId={story_data.projectId}")
        raise APIException(code=ErrorCode.BAD_REQUEST, message="编辑故事内容失败")
    
    app_logger.info(f"编辑故事内容成功: projectId={story_data.projectId}")
    return ResponseModel(code=200, message="修改成功", data=None)


@router.delete("/{projectId}", response_model=ResponseModel)
async def delete_story(
    projectId: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除故事内容接口

    - 需要JWT认证
    - 根据项目ID删除故事内容
    """
    app_logger.info(f"删除故事内容请求: projectId={projectId}")
    
    success = await story_service.delete_story(db, projectId, current_user["user_id"])
    if not success:
        app_logger.warning(f"删除故事内容失败: projectId={projectId}")
        raise APIException(code=ErrorCode.BAD_REQUEST, message="删除故事内容失败")
    
    app_logger.info(f"删除故事内容成功: projectId={projectId}")
    return ResponseModel(code=200, message="删除成功", data=None)


@router.get("/export/{projectId}")
async def export_story(
    projectId: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    故事导出接口

    - 需要JWT认证
    - 根据项目ID导出故事内容为.txt文件
    """
    app_logger.info(f"导出故事请求: projectId={projectId}")
    
    file_content, file_name = await story_service.export_story(db, projectId, current_user["user_id"])
    if not file_content:
        app_logger.warning(f"导出故事失败: projectId={projectId}")
        raise APIException(code=ErrorCode.NOT_FOUND, message="故事不存在")
    
    app_logger.info(f"导出故事成功: projectId={projectId}")
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=file_content,
        headers={
            "Content-Disposition": f"attachment; filename={file_name}",
            "Content-Type": "text/plain"
        }
    )


@router.post("/ai", response_model=ResponseModel)
async def generate_story_ai(
    ai_request: StoryAIRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    AI故事生成接口

    - 需要JWT认证
    - 根据主题、风格等参数生成故事内容
    """
    app_logger.info(f"AI故事生成请求: theme={ai_request.theme}")
    
    success = await story_service.generate_story_ai(
        db,
        ai_request.theme,
        ai_request.style,
        ai_request.keyword,
        ai_request.prompt,
        ai_request.number,
        ai_request.length,
        current_user["user_id"]
    )
    if not success:
        app_logger.warning(f"AI故事生成失败")
        raise APIException(code=ErrorCode.BAD_REQUEST, message="AI故事生成失败")
    
    app_logger.info(f"AI故事生成成功: theme={ai_request.theme}")
    return ResponseModel(code=200, message="生成成功", data=None)


@router.put("/ai", response_model=ResponseModel)
async def update_story_ai(
    ai_request: StoryAIUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    AI故事内容修改接口

    - 需要JWT认证
    - 根据项目ID和参数修改故事内容
    """
    app_logger.info(f"AI故事内容修改请求: projectId={ai_request.projectId}")
    
    success = await story_service.update_story_ai(
        db,
        ai_request.projectId,
        ai_request.theme,
        ai_request.style,
        ai_request.keyword,
        ai_request.prompt,
        ai_request.number,
        ai_request.length,
        ai_request.rewrite,
        current_user["user_id"]
    )
    if not success:
        app_logger.warning(f"AI故事内容修改失败: projectId={ai_request.projectId}")
        raise APIException(code=ErrorCode.BAD_REQUEST, message="AI故事内容修改失败")
    
    app_logger.info(f"AI故事内容修改成功: projectId={ai_request.projectId}")
    return ResponseModel(code=200, message="修改成功", data=None)