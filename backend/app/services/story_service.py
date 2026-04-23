"""
故事导入模块服务

实现故事内容的创建、编辑、删除、获取、导出以及AI故事生成等业务逻辑
"""

import uuid
from typing import Dict, Optional, Tuple
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.audio import Story
from app.models.project import Project
from app.services.ai_service import ai_service


class StoryService:
    """
    故事服务类
    """

    async def get_story_by_project_id(self, db: AsyncSession, project_id: str, user_id: str) -> Optional[Dict]:
        """
        根据项目ID获取故事内容
        """
        # 先检查项目是否存在且属于当前用户
        project_result = await db.execute(
            select(Project).where(Project.project_id == project_id, Project.user_id == user_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            return None

        # 获取项目关联的故事内容
        story_result = await db.execute(
            select(Story).where(Story.project_id == project_id)
        )
        story = story_result.scalar_one_or_none()

        if not story:
            return None

        # 构建返回数据
        story_data = {
            "title": project.title,
            "content": story.content,
            "createTime": story.create_time.isoformat(),
            "updateTime": story.update_time.isoformat()
        }

        return story_data

    async def create_story(self, db: AsyncSession, project_id: str, title: str, content: str, user_id: str) -> bool:
        """
        创建故事内容
        """
        try:
            # 检查项目是否存在且属于当前用户
            project_result = await db.execute(
                select(Project).where(Project.project_id == project_id, Project.user_id == user_id)
            )
            project = project_result.scalar_one_or_none()
            if not project:
                return False

            # 检查项目是否已有故事
            existing_story_result = await db.execute(
                select(Story).where(Story.project_id == project_id)
            )
            existing_story = existing_story_result.scalar_one_or_none()
            if existing_story:
                return False

            # 创建单个故事
            story = Story(
                story_id=str(uuid.uuid4()),
                title=title,
                content=content,
                chapter_number=1,
                project_id=project_id
            )
            db.add(story)

            await db.commit()
            return True
        except Exception as e:
            print(f"创建故事失败: {e}")
            await db.rollback()
            return False

    async def update_story(self, db: AsyncSession, project_id: str, title: str, content: str, user_id: str) -> bool:
        """
        更新故事内容
        """
        try:
            # 先检查项目是否存在且属于当前用户
            project_result = await db.execute(
                select(Project).where(Project.project_id == project_id, Project.user_id == user_id)
            )
            project = project_result.scalar_one_or_none()
            if not project:
                return False

            # 获取项目关联的故事
            story_result = await db.execute(
                select(Story).where(Story.project_id == project_id)
            )
            story = story_result.scalar_one_or_none()
            if not story:
                return False

            # 更新项目标题
            if title:
                project.title = title
                story.title = title

            # 更新故事内容
            if content:
                story.content = content

            await db.commit()
            return True
        except Exception as e:
            print(f"更新故事失败: {e}")
            await db.rollback()
            return False

    async def delete_story(self, db: AsyncSession, project_id: str, user_id: str) -> bool:
        """
        删除故事内容
        """
        try:
            # 先检查项目是否存在且属于当前用户
            project_result = await db.execute(
                select(Project).where(Project.project_id == project_id, Project.user_id == user_id)
            )
            project = project_result.scalar_one_or_none()
            if not project:
                return False

            # 删除项目关联的所有故事章节
            story_result = await db.execute(
                select(Story).where(Story.project_id == project_id)
            )
            stories = story_result.scalars().all()
            for story in stories:
                await db.delete(story)

            await db.commit()
            return True
        except Exception as e:
            print(f"删除故事失败: {e}")
            await db.rollback()
            return False

    async def export_story(self, db: AsyncSession, project_id: str, user_id: str) -> Tuple[Optional[str], Optional[str]]:
        """
        导出故事内容为.txt文件
        """
        # 获取故事内容
        story_data = await self.get_story_by_project_id(db, project_id, user_id)
        if not story_data:
            return None, None

        # 生成文件名
        file_name = f"故事_{story_data['title']}.txt"
        # 构建文件内容
        file_content = f"标题: {story_data['title']}\n\n{story_data['content']}"

        return file_content, file_name

    async def generate_story_ai(self, db: AsyncSession, project_id: str, theme: str, style: str, keyword: str, prompt: str, number: str, length: str, user_id: str) -> bool:
        """
        AI故事生成
        """
        try:
            # 检查项目是否存在且属于当前用户
            project_result = await db.execute(
                select(Project).where(Project.project_id == project_id, Project.user_id == user_id)
            )
            project = project_result.scalar_one_or_none()
            if not project:
                return False

            # 调用AI服务生成故事
            story_content = await ai_service.generate_story(
                theme=theme,
                style=style,
                keyword=keyword,
                prompt=prompt,
                number=number,
                length=length
            )

            if not story_content:
                return False

            # 检查项目是否已有故事
            existing_story_result = await db.execute(
                select(Story).where(Story.project_id == project_id)
            )
            existing_story = existing_story_result.scalar_one_or_none()

            if existing_story:
                # 更新现有故事
                existing_story.title = f"AI生成故事 - {theme}"
                existing_story.content = story_content
            else:
                # 创建新故事
                story = Story(
                    story_id=str(uuid.uuid4()),
                    title=f"AI生成故事 - {theme}",
                    content=story_content,
                    chapter_number=1,
                    project_id=project_id
                )
                db.add(story)

            # 更新项目信息
            project.title = f"AI生成故事 - {theme}"
            if style:
                project.style = style

            await db.commit()
            return True
        except Exception as e:
            print(f"AI故事生成失败: {e}")
            await db.rollback()
            return False

    async def update_story_ai(self, db: AsyncSession, project_id: str, theme: str, style: str, keyword: str, prompt: str, number: str, length: str, rewrite: bool, user_id: str) -> bool:
        """
        AI故事内容修改
        """
        try:
            # 先检查项目是否存在且属于当前用户
            project_result = await db.execute(
                select(Project).where(Project.project_id == project_id, Project.user_id == user_id)
            )
            project = project_result.scalar_one_or_none()
            if not project:
                return False

            # 获取当前故事内容
            story_result = await db.execute(
                select(Story).where(Story.project_id == project_id)
            )
            story = story_result.scalar_one_or_none()

            # 构建AI提示
            ai_prompt = prompt
            if not rewrite and story:
                # 如果不是重写，将当前故事内容作为参考
                ai_prompt = f"基于以下故事内容进行修改: {story.content}\n\n修改要求: {prompt}"

            # 调用AI服务生成新的故事内容
            story_content = await ai_service.generate_story(
                theme=theme or project.title,
                style=style or project.style,
                keyword=keyword,
                prompt=ai_prompt,
                number=number,
                length=length
            )

            if not story_content:
                return False

            if story:
                # 更新现有故事
                story.content = story_content
                if theme:
                    story.title = f"AI生成故事 - {theme}"
            else:
                # 创建新故事
                story = Story(
                    story_id=str(uuid.uuid4()),
                    title=f"AI生成故事 - {theme}",
                    content=story_content,
                    chapter_number=1,
                    project_id=project.project_id
                )
                db.add(story)

            # 更新项目信息
            if theme:
                project.title = f"AI生成故事 - {theme}"
            if style:
                project.style = style

            await db.commit()
            return True
        except Exception as e:
            print(f"AI故事内容修改失败: {e}")
            await db.rollback()
            return False




story_service = StoryService()