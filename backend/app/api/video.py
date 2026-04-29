from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.common import ResponseModel
from app.services.video_service import video_service
from app.services.prompt_engine import prompt_engine

router = APIRouter(prefix="/api/video", tags=["视频生成"])


@router.post("/generate", response_model=ResponseModel)
async def generate_video(
    project_id: str = Form(...),
    image: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
    duration: Optional[int] = Form(4),
    resolution: Optional[str] = Form("720p"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    optimized_prompt = prompt
    if prompt:
        optimized_prompt = await prompt_engine.optimize_prompt(prompt)
    
    image_content = await image.read()
    
    result = await video_service.create_video_task(
        db=db,
        user_id=current_user.user_id,
        project_id=project_id,
        image_content=image_content,
        prompt=optimized_prompt,
        duration=duration,
        resolution=resolution
    )
    
    return ResponseModel(code=200, message="视频生成任务已创建", data=result)


@router.get("/status/{task_id}", response_model=ResponseModel)
async def get_video_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    result = await video_service.get_task_status(db, task_id)
    return ResponseModel(code=200, message="查询成功", data=result)


@router.get("/list/{project_id}", response_model=ResponseModel)
async def list_project_videos(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    videos = await video_service.list_project_videos(db, project_id)
    return ResponseModel(code=200, message="查询成功", data=videos)
