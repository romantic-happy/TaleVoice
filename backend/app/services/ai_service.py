"""
AI服务模块

实现与大语言模型的交互，用于生成故事内容
"""

import asyncio
from typing import Optional, Dict, List

import openai

from app.core.config import settings


class AIService:
    """
    AI服务类
    """

    def __init__(self):
        """
        初始化AI服务
        """
        # 从配置获取API密钥和base_url
        self.api_key = settings.OPENAI_API_KEY.get_secret_value() if settings.OPENAI_API_KEY else ""
        self.base_url = settings.OPENAI_BASE_URL
        
        if not self.api_key:
            print("警告: 未设置OPENAI_API_KEY")
        
        # 初始化OpenAI客户端
        openai.api_key = self.api_key
        if self.base_url:
            openai.api_base = self.base_url

    async def generate_story(self, theme: str, style: str, keyword: str, prompt: str, number: str, length: str) -> Optional[str]:
        """
        生成故事内容
        
        Args:
            theme: 故事主题
            style: 故事风格
            keyword: 关键词
            prompt: 要求
            number: 章节数量
            length: 每章长度
            
        Returns:
            生成的故事内容
        """
        try:
            # 构建提示词
            system_prompt = "你是一个专业的故事生成器，擅长根据用户提供的主题、风格和要求生成生动有趣的故事。"
            
            user_prompt = f"请根据以下要求生成一个故事：\n"
            user_prompt += f"主题：{theme}\n"
            
            if style:
                user_prompt += f"风格：{style}\n"
            if keyword:
                user_prompt += f"关键词：{keyword}\n"
            if number:
                user_prompt += f"章节数量：{number}\n"
            if length:
                user_prompt += f"每章长度：{length}\n"
            if prompt:
                user_prompt += f"要求：{prompt}\n"
            
            user_prompt += "\n请生成一个完整的故事，包含引人入胜的情节和生动的描写。"

            # 调用OpenAI API
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4000,
                temperature=0.7,
                n=1
            )

            # 提取生成的故事内容
            story_content = response.choices[0].message.content
            return story_content
        except Exception as e:
            print(f"AI故事生成失败: {e}")
            # 当API调用失败时，返回一个默认的故事内容
            return self._get_default_story(theme)

    def _get_default_story(self, theme: str) -> str:
        """
        当API调用失败时，返回一个默认的故事内容
        """
        default_stories = {
            "勇敢": "从前，有一个勇敢的小男孩，他名叫小明。一天，他在森林里迷路了，但他没有害怕，而是勇敢地寻找回家的路。在途中，他遇到了一只受伤的小鸟，他帮助小鸟包扎了伤口。小鸟为了感谢他，带领他找到了回家的路。从此，小明变得更加勇敢，成为了村里的小英雄。",
            "友谊": "在一个美丽的村庄里，住着两个好朋友，小红和小丽。她们每天一起上学，一起玩耍。有一天，小红生病了，不能去上学。小丽每天放学后都会去看望她，给她补课，陪她聊天。小红很快就康复了，她们的友谊也变得更加深厚。",
            "智慧": "从前，有一个聪明的国王，他想找一个继承人。他给所有的王子出了一个难题：用最少的钱装满一个房间。其他王子都用了很多钱，但都没有成功。只有最小的王子，他买了一支蜡烛，点燃后，烛光充满了整个房间。国王很高兴，把王位传给了他。",
            "善良": "在一个寒冷的冬天，一个贫穷的小女孩在街头卖火柴。她又冷又饿，却没有人买她的火柴。这时，一位善良的老奶奶走过来，给了她一些食物和钱。小女孩非常感动，她把剩下的火柴都送给了其他需要帮助的人。从此，她的生活变得越来越好。"
        }
        
        # 根据主题返回默认故事
        for key, value in default_stories.items():
            if key in theme:
                return value
        
        # 默认故事
        return f"从前，有一个关于{theme}的故事。很久很久以前，在一个遥远的地方，住着一群善良的人们。他们过着幸福的生活，直到有一天，一件神奇的事情发生了..."

    async def process_story_for_audio(self, story_content: str, voice_names: List[str], style: str, prompt: str) -> Optional[Dict]:
        """
        处理故事内容，生成适合语音合成的格式
        
        Args:
            story_content: 故事内容
            voice_names: 音色名称列表
            style: 风格
            prompt: 要求
            
        Returns:
            处理后的故事内容，格式为指定的JSON结构
        """
        try:
            # 构建提示词
            system_prompt = "你是一个专业的故事处理助手，擅长将故事内容处理为适合语音合成的格式。"
            
            user_prompt = f"请将以下故事内容处理为适合语音合成的格式：\n"
            user_prompt += f"故事内容：{story_content}\n"
            user_prompt += f"可用音色：{', '.join(voice_names)}\n"
            if style:
                user_prompt += f"风格：{style}\n"
            if prompt:
                user_prompt += f"要求：{prompt}\n"
            
            user_prompt += "\n请按照以下格式返回结果：\n"
            user_prompt += "{\n"
            user_prompt += "    \"meta\": {\n"
            user_prompt += "        \"title\": \"故事标题\",\n"
            user_prompt += "        \"total_roles\": 角色总数,\n"
            user_prompt += "        \"total_segments\": 片段总数,\n"
            user_prompt += "        \"roles\": [\n"
            user_prompt += "            {\n"
            user_prompt += "                \"role\": \"角色1\",\n"
            user_prompt += "                \"voice\": \"角色1对应的音色的voiceId\"\n"
            user_prompt += "            },\n"
            user_prompt += "            {\n"
            user_prompt += "                \"role\": \"角色2\",\n"
            user_prompt += "                \"voice\": \"角色2对应的音色的voiceId\"\n"
            user_prompt += "            }\n"
            user_prompt += "        ]\n"
            user_prompt += "    },\n"
            user_prompt += "    \"segments\": [\n"
            user_prompt += "        {\n"
            user_prompt += "            \"role\": \"角色1\",\n"
            user_prompt += "            \"lines\": \"角色1的台词\"\n"
            user_prompt += "        },\n"
            user_prompt += "        {\n"
            user_prompt += "            \"role\": \"角色2\",\n"
            user_prompt += "            \"lines\": \"角色2的台词\"\n"
            user_prompt += "        }\n"
            user_prompt += "    ]\n"
            user_prompt += "}\n"
            user_prompt += "\n请注意：\n"
            user_prompt += "1. 请根据故事内容识别角色，并为每个角色分配一个合适的音色\n"
            user_prompt += "2. 请将故事内容分割为多个片段，每个片段只包含一个角色的台词\n"
            user_prompt += "3. 请确保返回的JSON格式正确，没有语法错误\n"

            # 调用OpenAI API
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4000,
                temperature=0.7,
                n=1
            )

            # 提取生成的内容
            processed_content = response.choices[0].message.content
            
            # 解析JSON
            import json
            return json.loads(processed_content)
        except Exception as e:
            print(f"处理故事内容失败: {e}")
            # 当API调用失败时，返回一个默认的处理结果
            return self._get_default_processed_story(story_content, voice_names)

    def _get_default_processed_story(self, story_content: str, voice_names: List[str]) -> Dict:
        """
        当API调用失败时，返回一个默认的处理结果
        """
        # 简单的默认处理逻辑
        roles = []
        for i, voice_name in enumerate(voice_names):
            roles.append({
                "role": f"角色{i+1}",
                "voice": f"voice_{i+1}"
            })
        
        # 简单的片段分割
        segments = []
        lines = story_content.split('。')
        for i, line in enumerate(lines):
            if line.strip():
                segments.append({
                    "role": f"角色{(i % len(roles)) + 1}",
                    "lines": line.strip() + "。"
                })
        
        return {
            "meta": {
                "title": "默认故事标题",
                "total_roles": len(roles),
                "total_segments": len(segments),
                "roles": roles
            },
            "segments": segments
        }

    async def process_story_for_images(self, story_content: str, style: str, prompt: str) -> Optional[Dict]:
        """
        处理故事内容，生成适合插图生成的提示
        
        Args:
            story_content: 故事内容
            style: 风格
            prompt: 要求
            
        Returns:
            处理后的故事内容，包含角色信息和场景描述
        """
        try:
            # 构建提示词
            system_prompt = "你是一个专业的故事分镜师，擅长将故事内容转化为适合插图生成的分镜和场景描述。"
            
            user_prompt = f"请将以下故事内容处理为适合插图生成的格式：\n"
            user_prompt += f"故事内容：{story_content}\n"
            user_prompt += f"风格：{style}\n"
            if prompt:
                user_prompt += f"要求：{prompt}\n"
            
            user_prompt += "\n请按照以下格式返回结果：\n"
            user_prompt += "{\n"
            user_prompt += "    \"characters\": [\n"
            user_prompt += "        {\n"
            user_prompt += "            \"name\": \"角色名称\",\n"
            user_prompt += "            \"description\": \"角色详细描述，包括外貌、性格等\"\n"
            user_prompt += "        }\n"
            user_prompt += "    ],\n"
            user_prompt += "    \"scenes\": [\n"
            user_prompt += "        {\n"
            user_prompt += "            \"id\": 1,\n"
            user_prompt += "            \"description\": \"场景描述，包括环境、氛围等\",\n"
            user_prompt += "            \"prompt\": \"适合AI图像生成的详细提示词\"\n"
            user_prompt += "        }\n"
            user_prompt += "    ]\n"
            user_prompt += "}\n"
            user_prompt += "\n请注意：\n"
            user_prompt += "1. 请识别故事中的主要角色，并提供详细的角色描述\n"
            user_prompt += "2. 请将故事内容分解为多个场景，每个场景对应一个插图\n"
            user_prompt += "3. 请为每个场景提供详细的描述和适合AI图像生成的提示词\n"
            user_prompt += "4. 请确保返回的JSON格式正确，没有语法错误\n"

            # 调用OpenAI API
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4000,
                temperature=0.7,
                n=1
            )

            # 提取生成的内容
            processed_content = response.choices[0].message.content
            
            # 解析JSON
            import json
            return json.loads(processed_content)
        except Exception as e:
            print(f"处理故事内容失败: {e}")
            # 当API调用失败时，返回一个默认的处理结果
            return self._get_default_processed_images(story_content, style)

    def _get_default_processed_images(self, story_content: str, style: str) -> Dict:
        """
        当API调用失败时，返回一个默认的处理结果
        """
        # 简单的默认处理逻辑
        characters = [
            {
                "name": "主角",
                "description": "一个勇敢的年轻人，穿着普通的衣服，有着坚定的眼神"
            }
        ]
        
        scenes = [
            {
                "id": 1,
                "description": "故事的开始场景",
                "prompt": f"一个勇敢的年轻人站在一个美丽的场景中，{style}风格，详细的环境描述，高质量的插图"
            }
        ]
        
        return {
            "characters": characters,
            "scenes": scenes
        }


ai_service = AIService()