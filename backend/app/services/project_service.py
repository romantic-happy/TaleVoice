"""
项目服务层

处理项目相关的业务逻辑，包括创建、更新、删除和查询项目
"""

import uuid
from typing import Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import Project


class ProjectService:
    """项目服务类，提供项目相关的业务逻辑处理"""

    @staticmethod
    async def get_project_by_id(db: AsyncSession, project_id: str) -> Optional[Project]:
        """
        根据项目ID查询项目

        Args:
            db: 数据库会话
            project_id: 项目ID

        Returns:
            Optional[Project]: 找到返回Project对象，否则返回None
        """
        result = await db.execute(select(Project).where(Project.project_id == project_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_projects_by_user(
        db: AsyncSession,
        user_id: str,
        page: int = 1,
        page_size: int = 10,
        title: Optional[str] = None
    ) -> Tuple[List[Project], int]:
        """
        获取用户项目列表（分页）

        Args:
            db: 数据库会话
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            title: 搜索关键词（支持部分匹配）

        Returns:
            Tuple[List[Project], int]: 项目列表和总数
        """
        query = select(Project).where(Project.user_id == user_id)

        if title:
            query = query.where(Project.title.like(f"%{title}%"))

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # 获取分页数据
        paginated_query = query.order_by(Project.create_time.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size)
        result = await db.execute(paginated_query)
        projects = result.scalars().all()

        return projects, total

    @staticmethod
    async def create_project(
        db: AsyncSession,
        user_id: str,
        title: str,
        description: Optional[str] = None,
        style: Optional[str] = None
    ) -> Project:
        """
        创建新项目

        Args:
            db: 数据库会话
            user_id: 所属用户ID
            title: 项目标题
            description: 项目描述
            style: 项目风格

        Returns:
            Project: 创建的项目对象
        """
        project = Project(
            project_id=str(uuid.uuid4()),
            title=title,
            description=description,
            style=style,
            user_id=user_id
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project

    @staticmethod
    async def update_project(
        db: AsyncSession,
        project_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        style: Optional[str] = None
    ) -> Optional[Project]:
        """
        更新项目信息

        Args:
            db: 数据库会话
            project_id: 项目ID
            title: 新标题
            description: 新描述
            style: 新风格

        Returns:
            Optional[Project]: 更新成功返回项目对象，不存在返回None
        """
        project = await ProjectService.get_project_by_id(db, project_id)
        if not project:
            return None

        if title is not None:
            project.title = title
        if description is not None:
            project.description = description
        if style is not None:
            project.style = style

        await db.commit()
        await db.refresh(project)
        return project

    @staticmethod
    async def delete_project(db: AsyncSession, project_id: str) -> bool:
        """
        删除项目

        Args:
            db: 数据库会话
            project_id: 项目ID

        Returns:
            bool: 删除成功返回True，不存在返回False
        """
        project = await ProjectService.get_project_by_id(db, project_id)
        if not project:
            return False

        await db.delete(project)
        await db.commit()
        return True


project_service = ProjectService()
