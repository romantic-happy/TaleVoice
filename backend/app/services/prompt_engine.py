from typing import Optional
from enum import Enum
from app.core.config import settings


class AIProviderType(str, Enum):
    MOCK = "mock"
    ALIYUN = "aliyun"
    DEFAULT = "default"


PROVIDER_PROMPT_STYLES = {
    AIProviderType.ALIYUN: {
        "prefix": "",
        "suffix": "高质量视频, 流畅运动, 电影质感",
        "max_length": 500,
        "prefer_simple": False,
        "support_chinese": True
    },
    AIProviderType.MOCK: {
        "prefix": "",
        "suffix": "high quality",
        "max_length": 500,
        "prefer_simple": True
    },
    AIProviderType.DEFAULT: {
        "prefix": "",
        "suffix": "high quality, smooth motion",
        "max_length": 500,
        "prefer_simple": True
    }
}


class PromptEngine:
    def __init__(self, provider_type: AIProviderType = None):
        if provider_type is None:
            provider_type = self._get_provider_type()
        self.provider_type = provider_type
        self.style = PROVIDER_PROMPT_STYLES.get(provider_type, PROVIDER_PROMPT_STYLES[AIProviderType.DEFAULT])

    def _get_provider_type(self) -> AIProviderType:
        provider = settings.AI_PROVIDER.lower()
        if provider == "aliyun":
            return AIProviderType.ALIYUN
        return AIProviderType.MOCK

    async def optimize_prompt(self, prompt: str) -> str:
        if not prompt:
            return prompt

        optimized = prompt.strip()

        prefix = self.style.get("prefix", "")
        suffix = self.style.get("suffix", "")
        max_length = self.style.get("max_length", 500)

        if prefix:
            optimized = f"{prefix} {optimized}"
        if suffix:
            optimized = f"{optimized}, {suffix}"

        if len(optimized) > max_length:
            optimized = optimized[:max_length]

        return optimized

    async def analyze_emotion(self, text: str) -> str:
        positive_words = ["快乐", "幸福", "开心", "高兴", "温暖", "爱", "美好"]
        negative_words = ["悲伤", "难过", "痛苦", "孤独", "恐惧", "愤怒"]
        neutral_words = ["平静", "安宁", "普通", "日常"]

        text_lower = text.lower()
        
        for word in positive_words:
            if word in text_lower:
                return "positive"
        for word in negative_words:
            if word in text_lower:
                return "negative"
        
        return "neutral"

    async def extract_scenes(self, text: str) -> list:
        scenes = []
        scene_keywords = ["森林", "城堡", "海边", "山", "花园", "房间", "街道", "天空"]
        
        text_lower = text.lower()
        for keyword in scene_keywords:
            if keyword in text_lower:
                scenes.append(keyword)
        
        return scenes


prompt_engine = PromptEngine()
