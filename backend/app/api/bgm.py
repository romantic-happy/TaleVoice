from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.common import ResponseModel
from app.services.bgm_service import bgm_processor

router = APIRouter(prefix="/api/bgm", tags=["背景音乐"])


@router.get("/list", response_model=ResponseModel)
async def list_bgm(
    style: Optional[str] = None,
    emotion: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    bgm_list = await bgm_processor.list_bgm(db, style=style, emotion=emotion)
    return ResponseModel(code=200, message="查询成功", data=bgm_list)


@router.get("/{bgm_id}", response_model=ResponseModel)
async def get_bgm_detail(
    bgm_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    bgm = await bgm_processor.get_bgm_by_id(db, bgm_id)
    if not bgm:
        raise HTTPException(status_code=404, detail="背景音乐不存在")
    return ResponseModel(code=200, message="查询成功", data=bgm)


@router.post("/recommend", response_model=ResponseModel)
async def recommend_bgm(
    story_content: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    recommendations = await bgm_processor.recommend_bgm(db, story_content)
    return ResponseModel(code=200, message="推荐成功", data=recommendations)
