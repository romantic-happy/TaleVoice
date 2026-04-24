"""
提示词优化引擎 v2.0

将故事文本转化为适合AI视频生成模型的结构化提示词
包括情感分析、场景提取、角色识别、动作提取、镜头语言生成等功能
支持多种AI服务商的提示词适配
"""

import re
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
from enum import Enum

from app.core.logger import app_logger


class AIProviderType(str, Enum):
    """AI服务商类型枚举"""
    MOCK = "mock"
    ALIYUN = "aliyun"
    DEFAULT = "default"


@dataclass
class PromptResult:
    """
    提示词优化结果数据类

    Attributes:
        original_text: 原始输入文本
        optimized_prompt: 优化后的英文提示词
        negative_prompt: 负面提示词(排除不期望的元素)
        emotion: 识别的主情感标签
        secondary_emotions: 次要情感列表
        scene_description: 提取的场景描述
        characters: 识别的角色列表
        actions: 识别的动作列表
        camera_movements: 镜头运动描述
        style_tags: 风格标签列表
        provider: 适配的AI服务商
    """
    original_text: str
    optimized_prompt: str
    negative_prompt: str
    emotion: str = "温馨"
    secondary_emotions: List[str] = field(default_factory=list)
    scene_description: str = ""
    characters: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    camera_movements: List[str] = field(default_factory=list)
    style_tags: List[str] = field(default_factory=list)
    provider: str = "default"


EMOTION_CONFIG = {
    "温馨": {
        "style": "warm and gentle",
        "atmosphere": "cozy and dreamy atmosphere, soft warm lighting, golden hour",
        "camera": "gentle camera movement, slow zoom in, soft focus",
        "bpm_range": (60, 80),
        "color_palette": "warm tones, soft pastels, cream and gold",
        "mood_keywords": ["peaceful", "heartwarming", "tender", "loving"]
    },
    "欢快": {
        "style": "cheerful and lively",
        "atmosphere": "bright and joyful atmosphere, vibrant saturated colors, sunny day",
        "camera": "dynamic camera movement, smooth pan, playful tracking shot",
        "bpm_range": (100, 130),
        "color_palette": "bright primary colors, rainbow accents, sunny yellows",
        "mood_keywords": ["happy", "playful", "energetic", "fun"]
    },
    "紧张": {
        "style": "suspenseful and intense",
        "atmosphere": "dramatic atmosphere, sharp shadows, high contrast lighting",
        "camera": "slow tracking shot, building tension, dramatic angles",
        "bpm_range": (80, 110),
        "color_palette": "dark blues, deep purples, stark contrasts",
        "mood_keywords": ["suspenseful", "dramatic", "intense", "gripping"]
    },
    "神秘": {
        "style": "mysterious and magical",
        "atmosphere": "ethereal and enchanting atmosphere, soft magical glow, sparkles",
        "camera": "slow floating movement, mystical reveal, dreamlike motion",
        "bpm_range": (70, 90),
        "color_palette": "deep purples, midnight blues, silver highlights",
        "mood_keywords": ["magical", "enchanting", "mystical", "wonderous"]
    },
    "悲伤": {
        "style": "melancholic and touching",
        "atmosphere": "somber atmosphere, muted desaturated colors, soft overcast light",
        "camera": "slow pull back, gentle drift, contemplative stillness",
        "bpm_range": (50, 70),
        "color_palette": "muted grays, soft blues, faded earth tones",
        "mood_keywords": ["touching", "poignant", "emotional", "heartfelt"]
    },
    "惊奇": {
        "style": "amazing and wonderful",
        "atmosphere": "awe-inspiring atmosphere, brilliant colors, magical sparkles",
        "camera": "sweeping reveal, dramatic zoom out, wonder-filled perspective",
        "bpm_range": (90, 120),
        "color_palette": "brilliant golds, sparkling whites, vibrant rainbows",
        "mood_keywords": ["amazing", "wondrous", "spectacular", "breathtaking"]
    },
    "平静": {
        "style": "calm and serene",
        "atmosphere": "peaceful atmosphere, soft natural lighting, gentle breeze",
        "camera": "smooth steady shot, gentle pan, tranquil movement",
        "bpm_range": (50, 70),
        "color_palette": "soft greens, gentle blues, natural earth tones",
        "mood_keywords": ["peaceful", "serene", "tranquil", "calm"]
    }
}

EMOTION_KEYWORDS = {
    "温馨": {
        "primary": ["温暖", "温馨", "幸福", "家", "爱", "拥抱", "微笑", "阳光", "月光", "摇篮", "妈妈", "爸爸", "奶奶", "爷爷", "亲人", "团圆", "祝福"],
        "secondary": ["柔和", "甜蜜", "亲切", "关怀", "陪伴", "守护", "温暖", "安心"],
        "weight": {"primary": 2.0, "secondary": 1.0}
    },
    "欢快": {
        "primary": ["快乐", "欢笑", "跳跃", "奔跑", "歌唱", "舞蹈", "游戏", "节日", "庆祝", "派对", "礼物", "惊喜", "开心", "高兴"],
        "secondary": ["活泼", "热闹", "有趣", "好玩", "兴奋", "喜悦", "欢呼"],
        "weight": {"primary": 2.0, "secondary": 1.0}
    },
    "紧张": {
        "primary": ["危险", "追逐", "黑暗", "风暴", "战斗", "逃跑", "恐惧", "紧张", "冒险", "危机", "怪物", "恶龙", "陷阱"],
        "secondary": ["惊险", "刺激", "悬念", "紧张", "压迫", "威胁", "挑战"],
        "weight": {"primary": 2.0, "secondary": 1.0}
    },
    "神秘": {
        "primary": ["魔法", "奇幻", "仙境", "精灵", "咒语", "宝藏", "秘密", "神秘", "古老", "传说", "神话", "魔法师", "巫师", "仙女"],
        "secondary": ["神奇", "不可思议", "玄妙", "奥秘", "魔力", "幻境"],
        "weight": {"primary": 2.0, "secondary": 1.0}
    },
    "悲伤": {
        "primary": ["离别", "失去", "哭泣", "孤独", "思念", "遗憾", "伤心", "落泪", "消逝", "死亡", "分离", "告别"],
        "secondary": ["忧伤", "难过", "心痛", "凄凉", "哀愁", "惆怅"],
        "weight": {"primary": 2.0, "secondary": 1.0}
    },
    "惊奇": {
        "primary": ["惊奇", "惊讶", "奇迹", "不可思议", "震撼", "壮观", "宏伟", "神奇", "惊叹"],
        "secondary": ["意外", "惊喜", "不可思议", "超乎想象", "令人惊叹"],
        "weight": {"primary": 2.0, "secondary": 1.0}
    },
    "平静": {
        "primary": ["平静", "安宁", "宁静", "祥和", "安详", "恬静", "悠闲", "自在"],
        "secondary": ["舒适", "惬意", "放松", "安详", "从容"],
        "weight": {"primary": 2.0, "secondary": 1.0}
    }
}

SCENE_KEYWORDS = {
    "自然景观": {
        "森林": "a magical forest with tall ancient trees, dappled sunlight filtering through leaves",
        "大海": "a vast sparkling ocean with gentle waves, horizon stretching endlessly",
        "山": "majestic mountains rising into clouds, snow-capped peaks in the distance",
        "河流": "a gentle crystal-clear river winding through green meadows",
        "湖泊": "a serene lake reflecting the sky, surrounded by lush vegetation",
        "草原": "endless green meadows swaying in the breeze, wildflowers scattered throughout",
        "沙漠": "golden sand dunes stretching to the horizon, warm sunlight",
        "瀑布": "a magnificent waterfall cascading down rocky cliffs, mist rising",
        "花园": "a beautiful enchanted garden with colorful blooming flowers",
        "天空": "a wide open sky with soft fluffy clouds, birds flying freely"
    },
    "建筑场景": {
        "城堡": "a grand fairytale castle with towering spires, flags waving",
        "宫殿": "a magnificent golden palace with ornate decorations",
        "村庄": "a peaceful storybook village with cozy cottages and cobblestone paths",
        "房子": "a charming little house with a thatched roof and flower boxes",
        "洞穴": "a mysterious glowing cave with crystal formations",
        "桥梁": "an ancient stone bridge arching over a gentle stream",
        "塔楼": "a tall mystical tower reaching toward the sky",
        "学校": "a cheerful school building with a playground"
    },
    "室内场景": {
        "房间": "a cozy room with warm lighting and comfortable furniture",
        "厨房": "a warm kitchen filled with delicious aromas",
        "卧室": "a peaceful bedroom with soft bedding and gentle light",
        "书房": "a magical library filled with ancient books",
        "王座厅": "a grand throne room with golden decorations"
    }
}

TIME_KEYWORDS = {
    "早晨": "early morning light, golden sunrise, dew on grass",
    "上午": "bright morning sunshine, clear blue sky",
    "中午": "midday sun, bright overhead lighting",
    "下午": "warm afternoon light, long soft shadows",
    "傍晚": "golden hour, warm sunset colors, orange and pink sky",
    "夜晚": "night scene, moonlight, stars twinkling, dark blue sky",
    "深夜": "deep night, mysterious darkness, faint starlight"
}

WEATHER_KEYWORDS = {
    "晴天": "clear sunny day, bright blue sky",
    "阴天": "overcast sky, soft diffused light",
    "雨天": "gentle rain falling, puddles reflecting light",
    "雪天": "snow falling softly, white winter landscape",
    "雾天": "mysterious fog, soft misty atmosphere",
    "风天": "wind blowing, leaves and hair moving",
    "彩虹": "beautiful rainbow arcing across the sky"
}

CHARACTER_KEYWORDS = {
    "小女孩": {"en": "a little girl", "traits": ["young", "innocent", "curious"]},
    "小男孩": {"en": "a little boy", "traits": ["young", "energetic", "adventurous"]},
    "公主": {"en": "a beautiful princess", "traits": ["elegant", "graceful", "kind"]},
    "王子": {"en": "a handsome prince", "traits": ["brave", "noble", "charming"]},
    "王后": {"en": "a regal queen", "traits": ["wise", "elegant", "caring"]},
    "国王": {"en": "a wise king", "traits": ["noble", "powerful", "benevolent"]},
    "巫婆": {"en": "an old witch", "traits": ["mysterious", "magical"]},
    "魔法师": {"en": "a powerful wizard", "traits": ["wise", "magical", "mysterious"]},
    "仙女": {"en": "a beautiful fairy", "traits": ["magical", "glowing", "ethereal"]},
    "精灵": {"en": "a playful elf", "traits": ["magical", "mischievous", "pointed ears"]},
    "巨人": {"en": "a friendly giant", "traits": ["huge", "gentle", "kind"]},
    "小矮人": {"en": "a cheerful dwarf", "traits": ["short", "bearded", "hardworking"]},
    "动物": {
        "兔子": "a cute fluffy rabbit",
        "狐狸": "a clever fox",
        "熊": "a friendly bear",
        "狼": "a mysterious wolf",
        "鸟": "colorful singing birds",
        "鹿": "a graceful deer",
        "猫": "a cute cat",
        "狗": "a loyal dog",
        "蝴蝶": "beautiful butterflies",
        "鱼": "colorful fish swimming"
    }
}

ACTION_KEYWORDS = {
    "移动": {
        "走进": "walking into",
        "跑过": "running through",
        "飞过": "flying over",
        "跳过": "jumping over",
        "爬上": "climbing up",
        "跳下": "jumping down",
        "穿过": "passing through",
        "来到": "arriving at",
        "离开": "leaving",
        "追逐": "chasing"
    },
    "互动": {
        "看着": "looking at",
        "拿着": "holding",
        "拥抱": "hugging",
        "微笑": "smiling",
        "哭泣": "crying",
        "说话": "talking",
        "唱歌": "singing",
        "跳舞": "dancing",
        "玩耍": "playing",
        "睡觉": "sleeping"
    },
    "状态": {
        "穿着": "wearing",
        "戴着": "wearing",
        "拿着": "carrying",
        "骑着": "riding",
        "坐着": "sitting",
        "站着": "standing",
        "躺着": "lying down"
    }
}

COLOR_KEYWORDS = {
    "红色": "red", "蓝色": "blue", "绿色": "green", "黄色": "yellow",
    "金色": "golden", "银色": "silver", "白色": "white", "黑色": "black",
    "粉色": "pink", "紫色": "purple", "橙色": "orange", "棕色": "brown",
    "灰色": "gray", "彩虹色": "rainbow colored"
}

OBJECT_KEYWORDS = {
    "物品": {
        "帽子": "hood", "裙子": "dress", "鞋子": "shoes", "披风": "cloak",
        "王冠": "crown", "魔杖": "magic wand", "宝剑": "sword", "盾牌": "shield",
        "花": "flowers", "苹果": "apple", "宝石": "gem", "钥匙": "key",
        "书": "book", "灯笼": "lantern", "镜子": "mirror", "箱子": "treasure chest"
    }
}

CAMERA_MOVEMENTS = {
    "推镜头": "slow zoom in",
    "拉镜头": "slow zoom out",
    "左移": "pan left",
    "右移": "pan right",
    "上移": "tilt up",
    "下移": "tilt down",
    "环绕": "orbit around",
    "跟随": "tracking shot following",
    "升降": "crane shot",
    "静止": "static shot"
}

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

AGE_GROUP_TAGS = {
    "0-3": {
        "style": "simple shapes, bright primary colors, very gentle motion",
        "complexity": "minimal details, large simple forms",
        "content": "no scary elements, very soft and safe"
    },
    "3-6": {
        "style": "cute rounded characters, warm friendly colors, gentle motion",
        "complexity": "moderate details, clear simple shapes",
        "content": "friendly characters, positive themes"
    },
    "6-9": {
        "style": "detailed illustrations, adventurous scenes, dynamic motion",
        "complexity": "rich details, engaging compositions",
        "content": "exciting adventures, brave heroes"
    },
    "9-12": {
        "style": "sophisticated storytelling, rich atmospheric details",
        "complexity": "complex compositions, layered scenes",
        "content": "deeper narratives, character development"
    }
}

DEFAULT_NEGATIVE_PROMPT = (
    "horror elements, dark themes, scary faces, blood, violence, gore, "
    "distorted faces, deformed characters, ugly, low quality, blurry, "
    "watermark, text overlay, signature, logo, nsfw, inappropriate content, "
    "realistic photos, photorealistic people, uncanny valley, creepy, "
    "bad anatomy, extra limbs, missing limbs, floating objects"
)

STORY_RHYTHM_KEYWORDS = {
    "开场": {
        "keywords": ["从前", "很久以前", "有一天", "在很久很久以前", "从前有", "故事开始"],
        "camera": "wide establishing shot, slow reveal",
        "motion": "gentle introduction, calm beginning",
        "intensity": 0.3
    },
    "发展": {
        "keywords": ["然后", "接着", "于是", "后来", "不久", "有一天"],
        "camera": "smooth tracking shot, following the action",
        "motion": "moderate pace, steady progress",
        "intensity": 0.5
    },
    "高潮": {
        "keywords": ["突然", "就在这时", "危急时刻", "关键时刻", "终于", "就在那一瞬间", "惊险", "紧张"],
        "camera": "dynamic camera movement, quick cuts, dramatic angles",
        "motion": "fast paced, intense action, dramatic reveal",
        "intensity": 1.0
    },
    "转折": {
        "keywords": ["但是", "然而", "没想到", "出乎意料", "原来", "竟然", "忽然"],
        "camera": "dramatic zoom, reveal shot, perspective shift",
        "motion": "sudden change, surprising turn",
        "intensity": 0.8
    },
    "结局": {
        "keywords": ["最后", "从此", "最终", "故事的最后", "他们幸福地", "圆满结束"],
        "camera": "slow pull back, peaceful wide shot",
        "motion": "calm resolution, gentle ending",
        "intensity": 0.4
    }
}

PROMPT_TEMPLATES = {
    "温馨童话": {
        "prefix": "heartwarming children's storybook illustration,",
        "style": "soft watercolor style, gentle pastel colors",
        "atmosphere": "warm and cozy atmosphere, soft golden light",
        "suffix": "tender moment, sweet and touching, family friendly"
    },
    "冒险故事": {
        "prefix": "exciting adventure story illustration,",
        "style": "dynamic comic book style, bold colors",
        "atmosphere": "thrilling atmosphere, dramatic lighting",
        "suffix": "heroic moment, brave and inspiring, action packed"
    },
    "奇幻魔法": {
        "prefix": "magical fantasy illustration,",
        "style": "ethereal art style, glowing magical effects",
        "atmosphere": "enchanted atmosphere, sparkles and magic dust",
        "suffix": "mystical and wonderous, spellbinding visual"
    },
    "悬疑神秘": {
        "prefix": "mysterious story illustration,",
        "style": "atmospheric noir style, dramatic shadows",
        "atmosphere": "suspenseful atmosphere, mysterious lighting",
        "suffix": "intriguing and captivating, edge of seat"
    },
    "自然风光": {
        "prefix": "beautiful nature scene,",
        "style": "realistic landscape painting style",
        "atmosphere": "serene natural atmosphere, soft natural lighting",
        "suffix": "peaceful and tranquil, breathtaking scenery"
    }
}

INTENSITY_MODIFIERS = {
    "low": {
        "motion": "subtle, gentle, slow",
        "camera": "static, smooth, calm",
        "color": "muted, soft, pastel"
    },
    "medium": {
        "motion": "moderate, steady, flowing",
        "camera": "tracking, panning, smooth",
        "color": "balanced, harmonious, natural"
    },
    "high": {
        "motion": "dynamic, energetic, fast",
        "camera": "dramatic, sweeping, intense",
        "color": "vibrant, bold, striking"
    }
}

CONTEXT_TRANSITIONS = {
    ("温馨", "紧张"): "building tension from peaceful scene",
    ("紧张", "温馨"): "relief after tension, heartwarming resolution",
    ("欢快", "悲伤"): "emotional shift, bittersweet moment",
    ("悲伤", "欢快"): "joyful turnaround, happy ending",
    ("神秘", "惊奇"): "magical reveal, wondrous discovery",
    ("平静", "紧张"): "sudden danger, dramatic shift"
}


class PromptEngine:
    """
    提示词优化引擎类 v2.0

    将故事文本转化为结构化的AI视频生成提示词
    处理流程: 文本清洗 → 情感分析 → 场景提取 → 角色识别 → 动作提取 → 提示词构建 → 提示词增强 → AI服务商适配
    """

    @staticmethod
    def clean_text(text: str) -> str:
        """
        清洗文本，移除无效字符和多余空白

        Args:
            text: 原始文本

        Returns:
            str: 清洗后的文本
        """
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\u4e00-\u9fff，。！？、；：""''（）《》【】]', '', text)
        return text.strip()

    @staticmethod
    def analyze_emotion(text: str) -> Tuple[str, List[str], float]:
        """
        分析文本情感（支持混合情感识别）

        通过关键词匹配和权重计算识别文本的情感倾向

        Args:
            text: 输入文本

        Returns:
            Tuple[str, List[str], float]: (主情感, 次要情感列表, 置信度)
        """
        emotion_scores: Dict[str, float] = {}

        for emotion, config in EMOTION_KEYWORDS.items():
            score = 0.0
            for kw in config["primary"]:
                count = text.count(kw)
                score += count * config["weight"]["primary"]
            for kw in config["secondary"]:
                count = text.count(kw)
                score += count * config["weight"]["secondary"]
            emotion_scores[emotion] = score

        total_score = sum(emotion_scores.values())
        if total_score == 0:
            return "温馨", [], 0.5

        sorted_emotions = sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)
        primary_emotion = sorted_emotions[0][0]
        confidence = sorted_emotions[0][1] / total_score

        secondary_emotions = []
        for emotion, score in sorted_emotions[1:3]:
            if score > 0:
                secondary_emotions.append(emotion)

        return primary_emotion, secondary_emotions, confidence

    @staticmethod
    def extract_scenes(text: str) -> Dict[str, List[str]]:
        """
        提取场景信息（支持多类型场景识别）

        Args:
            text: 输入文本

        Returns:
            Dict[str, List[str]]: 场景类型到场景描述列表的映射
        """
        scenes: Dict[str, List[str]] = {
            "natural": [],
            "architecture": [],
            "interior": []
        }

        for category, keywords in SCENE_KEYWORDS.items():
            for cn_keyword, en_description in keywords.items():
                if cn_keyword in text:
                    if category == "自然景观":
                        scenes["natural"].append(en_description)
                    elif category == "建筑场景":
                        scenes["architecture"].append(en_description)
                    elif category == "室内场景":
                        scenes["interior"].append(en_description)

        return scenes

    @staticmethod
    def extract_time_and_weather(text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        提取时间和天气信息

        Args:
            text: 输入文本

        Returns:
            Tuple[Optional[str], Optional[str]]: (时间描述, 天气描述)
        """
        time_desc = None
        weather_desc = None

        for cn_keyword, en_description in TIME_KEYWORDS.items():
            if cn_keyword in text:
                time_desc = en_description
                break

        for cn_keyword, en_description in WEATHER_KEYWORDS.items():
            if cn_keyword in text:
                weather_desc = en_description
                break

        return time_desc, weather_desc

    @staticmethod
    def extract_characters(text: str) -> List[Dict[str, str]]:
        """
        提取角色信息

        Args:
            text: 输入文本

        Returns:
            List[Dict[str, str]]: 角色信息列表
        """
        characters = []

        for cn_keyword, info in CHARACTER_KEYWORDS.items():
            if cn_keyword in text:
                if cn_keyword == "动物":
                    for animal_cn, animal_en in info.items():
                        if animal_cn in text:
                            characters.append({
                                "cn": animal_cn,
                                "en": animal_en,
                                "type": "animal"
                            })
                elif isinstance(info, dict) and "en" in info:
                    characters.append({
                        "cn": cn_keyword,
                        "en": info["en"],
                        "type": "character",
                        "traits": info.get("traits", [])
                    })

        return characters

    @staticmethod
    def extract_actions(text: str) -> List[str]:
        """
        提取动作信息

        Args:
            text: 输入文本

        Returns:
            List[str]: 英文动作描述列表
        """
        actions = []

        for category, keywords in ACTION_KEYWORDS.items():
            for cn_keyword, en_description in keywords.items():
                if cn_keyword in text:
                    actions.append(en_description)

        return actions

    @staticmethod
    def translate_to_english(text: str) -> str:
        """
        将中文文本转化为英文提示词（增强版）

        Args:
            text: 中文文本

        Returns:
            str: 英文提示词
        """
        result = text

        for cn, en in COLOR_KEYWORDS.items():
            result = result.replace(cn, en)

        for category, keywords in OBJECT_KEYWORDS.items():
            for cn, en in keywords.items():
                result = result.replace(cn, en)

        for category, keywords in ACTION_KEYWORDS.items():
            for cn, en in keywords.items():
                result = result.replace(cn, en)

        for cn_keyword, info in CHARACTER_KEYWORDS.items():
            if cn_keyword != "动物" and isinstance(info, dict) and "en" in info:
                result = result.replace(cn_keyword, info["en"])

        for cn_keyword, en_description in TIME_KEYWORDS.items():
            result = result.replace(cn_keyword, "")

        for cn_keyword, en_description in WEATHER_KEYWORDS.items():
            result = result.replace(cn_keyword, "")

        for category, keywords in SCENE_KEYWORDS.items():
            for cn_keyword, en_description in keywords.items():
                result = result.replace(cn_keyword, "")

        result = re.sub(r'[^\w\s]', ' ', result)
        result = re.sub(r'\s+', ' ', result).strip()

        if any('\u4e00' <= c <= '\u9fff' for c in result):
            result = f"a storybook scene, {result}"

        return result

    @staticmethod
    def generate_camera_movement(
        emotion: str,
        actions: List[str],
        scene_type: str = "natural"
    ) -> List[str]:
        """
        根据情感和动作生成镜头运动描述

        Args:
            emotion: 主情感
            actions: 动作列表
            scene_type: 场景类型

        Returns:
            List[str]: 镜头运动描述列表
        """
        movements = []

        if emotion in EMOTION_CONFIG:
            movements.append(EMOTION_CONFIG[emotion]["camera"])

        if "running" in " ".join(actions) or "chasing" in " ".join(actions):
            movements.append("tracking shot following the action")
        elif "walking" in " ".join(actions):
            movements.append("smooth tracking shot")
        elif "flying" in " ".join(actions):
            movements.append("sweeping aerial shot")

        if scene_type == "architecture":
            movements.append("slow establishing shot")
        elif scene_type == "interior":
            movements.append("intimate close-up shots")

        return movements[:2] if movements else ["gentle camera movement"]

    @staticmethod
    def adapt_for_provider(
        prompt: str,
        provider: AIProviderType = AIProviderType.DEFAULT
    ) -> str:
        """
        根据AI服务商适配提示词

        不同AI服务商对提示词长度和格式有不同偏好

        Args:
            prompt: 原始提示词
            provider: AI服务商类型

        Returns:
            str: 适配后的提示词
        """
        config = PROVIDER_PROMPT_STYLES.get(provider, PROVIDER_PROMPT_STYLES[AIProviderType.DEFAULT])

        if len(prompt) > config["max_length"]:
            parts = prompt.split(", ")
            essential_parts = parts[:int(len(parts) * 0.7)]
            prompt = ", ".join(essential_parts)

        if config["prefix"]:
            prompt = f"{config['prefix']} {prompt}"
        if config["suffix"]:
            prompt = f"{prompt}, {config['suffix']}"

        return prompt

    @staticmethod
    def optimize(
        text: str,
        style: Optional[str] = None,
        target_age: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        provider: AIProviderType = AIProviderType.DEFAULT,
        prev_emotion: Optional[str] = None,
        use_template: bool = True
    ) -> PromptResult:
        """
        优化故事文本为AI视频生成提示词（增强版 v3.0）

        完整处理流程:
        1. 文本清洗
        2. 情感分析（支持混合情感）
        3. 故事节奏分析
        4. 场景提取（自然/建筑/室内）
        5. 时间和天气提取
        6. 角色识别
        7. 动作提取
        8. 镜头语言生成
        9. 动态权重计算
        10. 提示词构建
        11. 模板应用
        12. 智能负面提示词生成
        13. AI服务商适配

        Args:
            text: 故事文本
            style: 项目风格(可选)
            target_age: 目标年龄段(可选)
            custom_prompt: 用户自定义提示词(可选，优先级最高)
            provider: AI服务商类型
            prev_emotion: 前一段情感(用于上下文过渡)
            use_template: 是否使用模板系统

        Returns:
            PromptResult: 优化后的提示词结果
        """
        if custom_prompt:
            app_logger.info("[PromptEngine] 使用自定义提示词")
            return PromptResult(
                original_text=text,
                optimized_prompt=custom_prompt,
                negative_prompt=DEFAULT_NEGATIVE_PROMPT,
                emotion="自定义",
                provider=provider.value
            )

        cleaned_text = PromptEngine.clean_text(text)

        emotion, secondary_emotions, confidence = PromptEngine.analyze_emotion(cleaned_text)
        emotion_config = EMOTION_CONFIG.get(emotion, EMOTION_CONFIG["温馨"])

        rhythm, intensity, rhythm_config = PromptEngine.analyze_story_rhythm(cleaned_text)
        intensity_level = PromptEngine.get_intensity_level(intensity)
        intensity_modifiers = INTENSITY_MODIFIERS[intensity_level]

        scenes = PromptEngine.extract_scenes(cleaned_text)
        time_desc, weather_desc = PromptEngine.extract_time_and_weather(cleaned_text)
        characters = PromptEngine.extract_characters(cleaned_text)
        actions = PromptEngine.extract_actions(cleaned_text)

        scene_type = "natural" if scenes["natural"] else ("architecture" if scenes["architecture"] else "interior")
        camera_movements = PromptEngine.generate_camera_movement(emotion, actions, scene_type)

        if intensity_level == "high":
            camera_movements = [rhythm_config.get("camera", camera_movements[0])] + camera_movements[:1]

        translated_text = PromptEngine.translate_to_english(cleaned_text)

        dynamic_weights = PromptEngine.calculate_dynamic_weights(emotion, confidence, intensity)

        transition_desc = PromptEngine.generate_context_transition(prev_emotion, emotion)

        prompt_parts = [
            "Children's picture book style, storybook illustration",
            emotion_config["style"],
            translated_text
        ]

        all_scenes = scenes["natural"] + scenes["architecture"] + scenes["interior"]
        if all_scenes:
            prompt_parts.append(all_scenes[0])

        if time_desc:
            prompt_parts.append(time_desc)
        if weather_desc:
            prompt_parts.append(weather_desc)

        prompt_parts.append(emotion_config["atmosphere"])

        if characters:
            char_desc = characters[0]["en"]
            if len(characters) > 1:
                char_desc += f" with {characters[1]['en']}"
            prompt_parts.append(char_desc)

        if actions:
            prompt_parts.append(", ".join(actions[:2]))

        prompt_parts.extend(camera_movements)

        prompt_parts.append("Ken Burns effect, slow cinematic motion")
        prompt_parts.append("16:9 aspect ratio")
        prompt_parts.append(emotion_config["color_palette"])

        if intensity_modifiers:
            prompt_parts.append(f"{intensity_modifiers['motion']} motion")

        if target_age and target_age in AGE_GROUP_TAGS:
            age_config = AGE_GROUP_TAGS[target_age]
            prompt_parts.append(age_config["style"])
            prompt_parts.append(age_config["content"])

        if style and style != "default":
            prompt_parts.append(f"{style} art style")

        if transition_desc:
            prompt_parts.append(transition_desc)

        prompt_parts.append("high quality, detailed, professional illustration")

        optimized_prompt = ", ".join(part for part in prompt_parts if part)

        if use_template:
            template_name = PromptEngine.select_template(emotion, scenes, actions)
            optimized_prompt = PromptEngine.apply_template(
                template_name,
                optimized_prompt,
                emotion_config
            )

        optimized_prompt = PromptEngine.adapt_for_provider(optimized_prompt, provider)

        has_scary_elements = any(kw in text for kw in ["怪物", "恶龙", "黑暗", "恐惧"])
        dynamic_negative = PromptEngine.generate_dynamic_negative_prompt(
            emotion, target_age, has_scary_elements
        )

        scene_description = ", ".join(all_scenes) if all_scenes else "storybook scene"
        character_names = [c["en"] for c in characters]

        app_logger.info(
            f"[PromptEngine] 提示词优化完成 v3.0 - 情感: {emotion}(置信度:{confidence:.2f}), "
            f"节奏: {rhythm}(强度:{intensity:.2f}), 次要情感: {secondary_emotions}, "
            f"角色: {character_names}, 提示词长度: {len(optimized_prompt)}"
        )

        return PromptResult(
            original_text=text,
            optimized_prompt=optimized_prompt,
            negative_prompt=dynamic_negative,
            emotion=emotion,
            secondary_emotions=secondary_emotions,
            scene_description=scene_description,
            characters=character_names,
            actions=actions,
            camera_movements=camera_movements,
            style_tags=[emotion_config["style"], "picture-book", "children", "storybook", rhythm],
            provider=provider.value
        )


    @staticmethod
    def analyze_story_rhythm(text: str) -> Tuple[str, float, Dict[str, str]]:
        """
        分析故事节奏（识别开场/发展/高潮/转折/结局）

        Args:
            text: 输入文本

        Returns:
            Tuple[str, float, Dict[str, str]]: (节奏阶段, 强度值, 节奏配置)
        """
        for rhythm, config in STORY_RHYTHM_KEYWORDS.items():
            for keyword in config["keywords"]:
                if keyword in text:
                    return rhythm, config["intensity"], {
                        "camera": config["camera"],
                        "motion": config["motion"]
                    }

        return "发展", 0.5, {
            "camera": "smooth tracking shot",
            "motion": "moderate pace"
        }

    @staticmethod
    def get_intensity_level(intensity: float) -> str:
        """
        根据强度值获取强度等级

        Args:
            intensity: 强度值 (0.0-1.0)

        Returns:
            str: 强度等级 (low/medium/high)
        """
        if intensity < 0.4:
            return "low"
        elif intensity < 0.7:
            return "medium"
        else:
            return "high"

    @staticmethod
    def generate_dynamic_negative_prompt(
        emotion: str,
        target_age: Optional[str] = None,
        has_scary_elements: bool = False
    ) -> str:
        """
        根据情感和内容动态生成负面提示词

        Args:
            emotion: 主情感
            target_age: 目标年龄段
            has_scary_elements: 是否包含恐怖元素

        Returns:
            str: 动态生成的负面提示词
        """
        base_negatives = [
            "low quality", "blurry", "watermark", "text overlay",
            "bad anatomy", "deformed", "ugly", "distorted"
        ]

        age_restrictions = {
            "0-3": ["any scary elements", "dark themes", "loud sounds", "fast motion"],
            "3-6": ["horror", "violence", "scary faces", "dark scenes"],
            "6-9": ["extreme violence", "gore", "blood"],
            "9-12": ["gore", "explicit content"]
        }

        emotion_specific = {
            "温馨": ["scary elements", "dark themes", "violence"],
            "欢快": ["sad elements", "dark themes", "scary faces"],
            "紧张": ["gore", "blood", "extreme violence"],
            "神秘": ["scary faces", "horror elements", "blood"],
            "悲伤": ["scary elements", "violence", "gore"],
            "惊奇": ["scary elements", "dark themes"],
            "平静": ["scary elements", "violence", "fast motion"]
        }

        negatives = base_negatives.copy()

        if emotion in emotion_specific:
            negatives.extend(emotion_specific[emotion])

        if target_age and target_age in age_restrictions:
            negatives.extend(age_restrictions[target_age])

        if has_scary_elements:
            negatives.extend(["realistic horror", "disturbing imagery"])

        negatives.extend([
            "nsfw", "inappropriate content", "realistic photos",
            "photorealistic people", "uncanny valley"
        ])

        seen = set()
        unique_negatives = []
        for neg in negatives:
            if neg not in seen:
                seen.add(neg)
                unique_negatives.append(neg)

        return ", ".join(unique_negatives)

    @staticmethod
    def select_template(emotion: str, scenes: Dict[str, List[str]], actions: List[str]) -> str:
        """
        根据情感、场景和动作选择最佳提示词模板

        Args:
            emotion: 主情感
            scenes: 场景信息
            actions: 动作列表

        Returns:
            str: 模板名称
        """
        has_natural = len(scenes.get("natural", [])) > 0
        has_magic = any(kw in str(actions) for kw in ["magic", "spell", "fly"])
        has_adventure = any(kw in str(actions) for kw in ["running", "chasing", "jumping"])

        if emotion in ["神秘", "惊奇"] or has_magic:
            return "奇幻魔法"
        elif emotion == "紧张" or has_adventure:
            return "冒险故事"
        elif emotion in ["温馨", "平静"] and has_natural:
            return "自然风光"
        elif emotion in ["温馨", "欢快", "悲伤"]:
            return "温馨童话"
        else:
            return "温馨童话"

    @staticmethod
    def apply_template(
        template_name: str,
        base_prompt: str,
        emotion_config: Dict
    ) -> str:
        """
        应用提示词模板

        Args:
            template_name: 模板名称
            base_prompt: 基础提示词
            emotion_config: 情感配置

        Returns:
            str: 应用模板后的提示词
        """
        template = PROMPT_TEMPLATES.get(template_name, PROMPT_TEMPLATES["温馨童话"])

        parts = [
            template["prefix"],
            base_prompt,
            template["style"],
            template["atmosphere"],
            emotion_config.get("color_palette", ""),
            template["suffix"]
        ]

        return ", ".join(p for p in parts if p)

    @staticmethod
    def generate_context_transition(
        prev_emotion: Optional[str],
        current_emotion: str
    ) -> Optional[str]:
        """
        生成情感过渡描述

        Args:
            prev_emotion: 前一段情感
            current_emotion: 当前情感

        Returns:
            Optional[str]: 过渡描述，无过渡时返回None
        """
        if not prev_emotion or prev_emotion == current_emotion:
            return None

        transition_key = (prev_emotion, current_emotion)
        return CONTEXT_TRANSITIONS.get(transition_key)

    @staticmethod
    def calculate_dynamic_weights(
        emotion: str,
        confidence: float,
        intensity: float
    ) -> Dict[str, float]:
        """
        根据情感置信度和故事强度计算动态权重

        Args:
            emotion: 主情感
            confidence: 情感置信度
            intensity: 故事强度

        Returns:
            Dict[str, float]: 各元素权重配置
        """
        emotion_weight = confidence * 0.5 + 0.5
        intensity_weight = intensity

        return {
            "emotion_style": emotion_weight,
            "atmosphere": emotion_weight * 0.8,
            "camera_movement": intensity_weight,
            "color_palette": emotion_weight * 0.6,
            "scene_detail": 0.7 + intensity_weight * 0.3,
            "character_focus": 0.8 if confidence > 0.6 else 0.5,
            "action_emphasis": intensity_weight * 0.9
        }

    @staticmethod
    def generate_multiple_candidates(
        text: str,
        provider: AIProviderType = AIProviderType.DEFAULT,
        count: int = 3
    ) -> List["PromptResult"]:
        """
        生成多个候选提示词（用于A/B测试）

        Args:
            text: 故事文本
            provider: AI服务商
            count: 候选数量

        Returns:
            List[PromptResult]: 候选提示词列表
        """
        candidates = []

        base_result = PromptEngine.optimize(text, provider=provider)
        candidates.append(base_result)

        emotion, secondary_emotions, confidence = PromptEngine.analyze_emotion(text)
        scenes = PromptEngine.extract_scenes(text)

        if len(secondary_emotions) > 0:
            alt_emotion = secondary_emotions[0]
            alt_config = EMOTION_CONFIG.get(alt_emotion, EMOTION_CONFIG["温馨"])

            alt_prompt = base_result.optimized_prompt.replace(
                EMOTION_CONFIG.get(emotion, {})["style"],
                alt_config["style"]
            )
            alt_prompt = alt_prompt.replace(
                EMOTION_CONFIG.get(emotion, {})["atmosphere"],
                alt_config["atmosphere"]
            )

            candidates.append(PromptResult(
                original_text=text,
                optimized_prompt=PromptEngine.adapt_for_provider(alt_prompt, provider),
                negative_prompt=base_result.negative_prompt,
                emotion=alt_emotion,
                secondary_emotions=[emotion],
                scene_description=base_result.scene_description,
                characters=base_result.characters,
                actions=base_result.actions,
                camera_movements=base_result.camera_movements,
                style_tags=base_result.style_tags,
                provider=provider.value
            ))

        template_name = PromptEngine.select_template(emotion, scenes, base_result.actions)
        if template_name != "温馨童话":
            template = PROMPT_TEMPLATES[template_name]
            template_prompt = PromptEngine.apply_template(
                template_name,
                base_result.scene_description,
                EMOTION_CONFIG.get(emotion, EMOTION_CONFIG["温馨"])
            )

            candidates.append(PromptResult(
                original_text=text,
                optimized_prompt=PromptEngine.adapt_for_provider(template_prompt, provider),
                negative_prompt=base_result.negative_prompt,
                emotion=emotion,
                secondary_emotions=base_result.secondary_emotions,
                scene_description=base_result.scene_description,
                characters=base_result.characters,
                actions=base_result.actions,
                camera_movements=base_result.camera_movements,
                style_tags=[template["style"]] + base_result.style_tags,
                provider=provider.value
            ))

        return candidates[:count]


prompt_engine = PromptEngine()
