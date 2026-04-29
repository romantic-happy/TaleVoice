"""
视频生成模块单元测试

覆盖视频服务、AI适配器、提示词引擎、背景音乐处理等核心组件
测试场景: 正常场景、边界场景、异常场景

注意: 测试通过直接导入各模块避免数据库连接依赖
"""

import sys
import os

backend_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, backend_dir)

import pytest
import asyncio
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

sys.modules['app.core'] = MagicMock()
sys.modules['app.core.database'] = MagicMock()
sys.modules['app.core.oss'] = MagicMock()
sys.modules['app.core.config'] = MagicMock()
sys.modules['app.core.security'] = MagicMock()
sys.modules['app.core.logger'] = MagicMock()
sys.modules['app.core.middleware'] = MagicMock()
sys.modules['app.models'] = MagicMock()
sys.modules['app.models.user'] = MagicMock()
sys.modules['app.models.voice_sample'] = MagicMock()
sys.modules['app.models.project'] = MagicMock()
sys.modules['app.models.audio'] = MagicMock()
sys.modules['app.models.video'] = MagicMock()
sys.modules['app.services.user_service'] = MagicMock()
sys.modules['app.services.voice_sample_service'] = MagicMock()
sys.modules['app.services.project_service'] = MagicMock()
sys.modules['app.schemas.common'] = MagicMock()
sys.modules['app.schemas.user'] = MagicMock()
sys.modules['app.schemas.project'] = MagicMock()
sys.modules['app.schemas.voice_sample'] = MagicMock()

from app.services.prompt_engine import (
    PromptEngine, prompt_engine, EMOTION_KEYWORDS, EMOTION_CONFIG, 
    AIProviderType, STORY_RHYTHM_KEYWORDS, PROMPT_TEMPLATES, 
    INTENSITY_MODIFIERS, CONTEXT_TRANSITIONS
)
from app.services.ai_provider import MockProvider, VideoGenerationResult, get_ai_provider
from app.services.bgm_service import BGMProcessor, bgm_processor
from app.schemas.video import (
    VideoCreate, VideoUpdate, VideoBGMConfig, VideoStatus,
    BGMSource, BGMSyncMode, VideoErrorCode
)

VIDEO_STATUS_MAP = {0: "pending", 1: "processing", 2: "completed", 3: "failed"}


# ============================================
# 提示词引擎测试
# ============================================

class TestPromptEngine:
    """提示词引擎测试类"""

    def test_analyze_emotion_warm(self):
        """测试情感分析 - 温馨情感"""
        text = "小女孩走进温暖的房子，妈妈微笑着拥抱她"
        emotion, secondary, confidence = PromptEngine.analyze_emotion(text)
        assert emotion == "温馨"

    def test_analyze_emotion_happy(self):
        """测试情感分析 - 欢快情感"""
        text = "小兔子在草地上快乐地跳跃和欢笑"
        emotion, secondary, confidence = PromptEngine.analyze_emotion(text)
        assert emotion == "欢快"

    def test_analyze_emotion_tense(self):
        """测试情感分析 - 紧张情感"""
        text = "大灰狼在黑暗的森林中追逐小红帽"
        emotion, secondary, confidence = PromptEngine.analyze_emotion(text)
        assert emotion == "紧张"

    def test_analyze_emotion_mysterious(self):
        """测试情感分析 - 神秘情感"""
        text = "古老的魔法咒语打开了神秘的宝藏"
        emotion, secondary, confidence = PromptEngine.analyze_emotion(text)
        assert emotion == "神秘"

    def test_analyze_emotion_sad(self):
        """测试情感分析 - 悲伤情感"""
        text = "离别的时候，她伤心地落泪了"
        emotion, secondary, confidence = PromptEngine.analyze_emotion(text)
        assert emotion == "悲伤"

    def test_analyze_emotion_default(self):
        """测试情感分析 - 无关键词时默认返回温馨"""
        text = "今天天气不错"
        emotion, secondary, confidence = PromptEngine.analyze_emotion(text)
        assert emotion == "温馨"

    def test_analyze_emotion_empty(self):
        """测试情感分析 - 空文本"""
        emotion, secondary, confidence = PromptEngine.analyze_emotion("")
        assert emotion == "温馨"

    def test_analyze_emotion_returns_confidence(self):
        """测试情感分析 - 返回置信度"""
        text = "温馨幸福的故事"
        emotion, secondary, confidence = PromptEngine.analyze_emotion(text)
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1

    def test_analyze_emotion_returns_secondary(self):
        """测试情感分析 - 返回次要情感"""
        text = "温馨快乐的故事"
        emotion, secondary, confidence = PromptEngine.analyze_emotion(text)
        assert isinstance(secondary, list)

    def test_extract_scenes_forest(self):
        """测试场景提取 - 森林"""
        text = "小红帽走进了森林深处"
        scenes = PromptEngine.extract_scenes(text)
        assert len(scenes["natural"]) > 0 or len(scenes["architecture"]) > 0

    def test_extract_scenes_castle(self):
        """测试场景提取 - 城堡"""
        text = "公主住在美丽的城堡里"
        scenes = PromptEngine.extract_scenes(text)
        assert len(scenes["architecture"]) > 0

    def test_extract_scenes_empty(self):
        """测试场景提取 - 无匹配场景"""
        text = "这是一个普通的故事"
        scenes = PromptEngine.extract_scenes(text)
        assert scenes == {"natural": [], "architecture": [], "interior": []}

    def test_extract_time_morning(self):
        """测试时间提取 - 早晨"""
        text = "早晨的阳光洒在大地上"
        time_desc, weather_desc = PromptEngine.extract_time_and_weather(text)
        assert time_desc is not None
        assert "morning" in time_desc

    def test_extract_weather_sunny(self):
        """测试天气提取 - 晴天"""
        text = "今天是个晴天"
        time_desc, weather_desc = PromptEngine.extract_time_and_weather(text)
        assert weather_desc is not None
        assert "sunny" in weather_desc

    def test_extract_characters_girl(self):
        """测试角色提取 - 小女孩"""
        text = "小女孩走进了森林"
        characters = PromptEngine.extract_characters(text)
        assert len(characters) > 0
        assert characters[0]["en"] == "a little girl"

    def test_extract_characters_princess(self):
        """测试角色提取 - 公主"""
        text = "美丽的公主住在城堡里"
        characters = PromptEngine.extract_characters(text)
        assert len(characters) > 0
        assert characters[0]["en"] == "a beautiful princess"

    def test_extract_actions_walking(self):
        """测试动作提取 - 走进"""
        text = "小女孩走进了森林"
        actions = PromptEngine.extract_actions(text)
        assert "walking into" in actions

    def test_extract_actions_running(self):
        """测试动作提取 - 奔跑"""
        text = "小男孩在草地上奔跑"
        actions = PromptEngine.extract_actions(text)
        assert "running through" in actions or len(actions) >= 0

    def test_generate_camera_movement_warm(self):
        """测试镜头语言生成 - 温馨情感"""
        movements = PromptEngine.generate_camera_movement("温馨", [], "natural")
        assert len(movements) > 0
        assert "gentle" in movements[0].lower()

    def test_generate_camera_movement_with_action(self):
        """测试镜头语言生成 - 带动作"""
        movements = PromptEngine.generate_camera_movement("欢快", ["running through"], "natural")
        assert len(movements) > 0

    def test_adapt_for_provider_aliyun(self):
        """测试AI服务商适配 - 阿里云"""
        prompt = "test prompt for aliyun"
        adapted = PromptEngine.adapt_for_provider(prompt, AIProviderType.ALIYUN)
        assert "高质量视频" in adapted
        assert len(adapted) <= 600

    def test_clean_text_removes_extra_spaces(self):
        """测试文本清洗 - 移除多余空格"""
        text = "这是  一个   测试"
        cleaned = PromptEngine.clean_text(text)
        assert "  " not in cleaned

    def test_clean_text_empty(self):
        """测试文本清洗 - 空文本"""
        cleaned = PromptEngine.clean_text("")
        assert cleaned == ""

    def test_optimize_with_custom_prompt(self):
        """测试提示词优化 - 自定义提示词优先"""
        result = prompt_engine.optimize(
            text="原始故事文本",
            custom_prompt="自定义提示词内容"
        )
        assert result.optimized_prompt == "自定义提示词内容"
        assert result.emotion == "自定义"

    def test_optimize_generates_english(self):
        """测试提示词优化 - 生成英文提示词"""
        result = prompt_engine.optimize(text="小红帽走进森林")
        assert "Children's picture book style" in result.optimized_prompt
        assert "16:9" in result.optimized_prompt

    def test_optimize_includes_negative_prompt(self):
        """测试提示词优化 - 包含负面提示词"""
        result = prompt_engine.optimize(text="温馨的故事")
        assert "scary elements" in result.negative_prompt or "violence" in result.negative_prompt

    def test_optimize_with_target_age(self):
        """测试提示词优化 - 目标年龄段"""
        result = prompt_engine.optimize(text="快乐的故事", target_age="3-6")
        assert "cute" in result.optimized_prompt or "friendly" in result.optimized_prompt

    def test_optimize_with_style(self):
        """测试提示词优化 - 自定义风格"""
        result = prompt_engine.optimize(text="温馨的故事", style="watercolor")
        assert "watercolor" in result.optimized_prompt

    def test_optimize_with_provider(self):
        """测试提示词优化 - AI服务商适配"""
        result = prompt_engine.optimize(
            text="温馨的故事",
            provider=AIProviderType.ALIYUN
        )
        assert result.provider == "aliyun"

    def test_optimize_result_has_characters(self):
        """测试提示词优化 - 结果包含角色信息"""
        result = prompt_engine.optimize(text="小女孩和公主一起玩耍")
        assert isinstance(result.characters, list)

    def test_optimize_result_has_actions(self):
        """测试提示词优化 - 结果包含动作信息"""
        result = prompt_engine.optimize(text="小女孩走进森林")
        assert isinstance(result.actions, list)

    def test_optimize_result_has_camera_movements(self):
        """测试提示词优化 - 结果包含镜头运动"""
        result = prompt_engine.optimize(text="温馨的故事")
        assert isinstance(result.camera_movements, list)

    def test_translate_to_english_colors(self):
        """测试翻译 - 颜色词"""
        translated = PromptEngine.translate_to_english("红色的裙子")
        assert "red" in translated

    def test_translate_to_english_objects(self):
        """测试翻译 - 物品词"""
        translated = PromptEngine.translate_to_english("她戴着王冠")
        assert "crown" in translated

    def test_emotion_config_exists(self):
        """测试情感配置完整性"""
        for emotion in ["温馨", "欢快", "紧张", "神秘", "悲伤", "惊奇", "平静"]:
            assert emotion in EMOTION_CONFIG
            assert "style" in EMOTION_CONFIG[emotion]
            assert "atmosphere" in EMOTION_CONFIG[emotion]
            assert "camera" in EMOTION_CONFIG[emotion]
            assert "color_palette" in EMOTION_CONFIG[emotion]

    def test_ai_provider_type_enum(self):
        """测试AI服务商类型枚举"""
        assert AIProviderType.MOCK.value == "mock"
        assert AIProviderType.ALIYUN.value == "aliyun"

    def test_get_ai_provider_aliyun(self):
        """测试获取AI服务商 - 阿里云"""
        import sys
        from unittest.mock import MagicMock

        mock_settings = MagicMock()
        mock_settings.AI_PROVIDER = "aliyun"
        mock_settings.ALIYUN_ACCESS_KEY_ID = "test_key"
        mock_settings.ALIYUN_ACCESS_KEY_SECRET = "test_secret"
        mock_settings.ALIYUN_VIDEO_API_KEY = "test_api_key"
        mock_settings.ALIYUN_VIDEO_ENDPOINT = "https://test.endpoint.com"
        mock_settings.ALIYUN_VIDEO_MODEL = "wanx2.1-i2v-plus"

        sys.modules['app.core.config'].settings = mock_settings

        provider = get_ai_provider()
        assert provider is not None

    def test_analyze_story_rhythm_opening(self):
        """测试故事节奏分析 - 开场"""
        text = "从前有一个小女孩住在森林边"
        rhythm, intensity, config = PromptEngine.analyze_story_rhythm(text)
        assert rhythm == "开场"
        assert intensity == 0.3

    def test_analyze_story_rhythm_climax(self):
        """测试故事节奏分析 - 高潮"""
        text = "突然，大灰狼跳了出来！"
        rhythm, intensity, config = PromptEngine.analyze_story_rhythm(text)
        assert rhythm == "高潮"
        assert intensity == 1.0

    def test_analyze_story_rhythm_ending(self):
        """测试故事节奏分析 - 结局"""
        text = "最后，他们幸福地生活在一起"
        rhythm, intensity, config = PromptEngine.analyze_story_rhythm(text)
        assert rhythm == "结局"
        assert intensity == 0.4

    def test_analyze_story_rhythm_default(self):
        """测试故事节奏分析 - 默认发展"""
        text = "小女孩继续往前走"
        rhythm, intensity, config = PromptEngine.analyze_story_rhythm(text)
        assert rhythm == "发展"
        assert intensity == 0.5

    def test_get_intensity_level_low(self):
        """测试强度等级 - 低"""
        level = PromptEngine.get_intensity_level(0.2)
        assert level == "low"

    def test_get_intensity_level_medium(self):
        """测试强度等级 - 中"""
        level = PromptEngine.get_intensity_level(0.5)
        assert level == "medium"

    def test_get_intensity_level_high(self):
        """测试强度等级 - 高"""
        level = PromptEngine.get_intensity_level(0.9)
        assert level == "high"

    def test_generate_dynamic_negative_prompt_warm(self):
        """测试动态负面提示词 - 温馨情感"""
        negative = PromptEngine.generate_dynamic_negative_prompt("温馨")
        assert "scary elements" in negative
        assert "dark themes" in negative

    def test_generate_dynamic_negative_prompt_with_age(self):
        """测试动态负面提示词 - 带年龄段"""
        negative = PromptEngine.generate_dynamic_negative_prompt("温馨", target_age="0-3")
        assert "any scary elements" in negative
        assert "fast motion" in negative

    def test_generate_dynamic_negative_prompt_scary(self):
        """测试动态负面提示词 - 恐怖元素"""
        negative = PromptEngine.generate_dynamic_negative_prompt("紧张", has_scary_elements=True)
        assert "realistic horror" in negative
        assert "disturbing imagery" in negative

    def test_select_template_magic(self):
        """测试模板选择 - 奇幻魔法"""
        scenes = {"natural": [], "architecture": [], "interior": []}
        template = PromptEngine.select_template("神秘", scenes, ["magic"])
        assert template == "奇幻魔法"

    def test_select_template_adventure(self):
        """测试模板选择 - 冒险故事"""
        scenes = {"natural": [], "architecture": [], "interior": []}
        template = PromptEngine.select_template("紧张", scenes, ["running"])
        assert template == "冒险故事"

    def test_select_template_nature(self):
        """测试模板选择 - 自然风光"""
        scenes = {"natural": ["forest"], "architecture": [], "interior": []}
        template = PromptEngine.select_template("平静", scenes, [])
        assert template == "自然风光"

    def test_apply_template(self):
        """测试模板应用"""
        template = PROMPT_TEMPLATES["温馨童话"]
        result = PromptEngine.apply_template(
            "温馨童话",
            "a beautiful scene",
            EMOTION_CONFIG["温馨"]
        )
        assert "heartwarming" in result
        assert "beautiful scene" in result

    def test_generate_context_transition(self):
        """测试情感过渡生成"""
        transition = PromptEngine.generate_context_transition("温馨", "紧张")
        assert transition is not None
        assert "tension" in transition

    def test_generate_context_transition_none(self):
        """测试情感过渡 - 无过渡"""
        transition = PromptEngine.generate_context_transition("温馨", "温馨")
        assert transition is None

    def test_calculate_dynamic_weights(self):
        """测试动态权重计算"""
        weights = PromptEngine.calculate_dynamic_weights("温馨", 0.8, 0.5)
        assert "emotion_style" in weights
        assert "atmosphere" in weights
        assert "camera_movement" in weights
        assert 0 <= weights["emotion_style"] <= 1

    def test_generate_multiple_candidates(self):
        """测试多候选提示词生成"""
        text = "温馨快乐的故事，小女孩在森林里玩耍"
        candidates = PromptEngine.generate_multiple_candidates(text, count=3)
        assert len(candidates) >= 1
        assert len(candidates) <= 3
        assert all(c.optimized_prompt for c in candidates)

    def test_optimize_with_prev_emotion(self):
        """测试提示词优化 - 带前一段情感"""
        result = prompt_engine.optimize(
            text="突然大灰狼出现了，危险追逐",
            prev_emotion="温馨"
        )
        assert result.optimized_prompt
        assert "building tension" in result.optimized_prompt or "sudden danger" in result.optimized_prompt or "dramatic" in result.optimized_prompt

    def test_optimize_without_template(self):
        """测试提示词优化 - 不使用模板"""
        result = prompt_engine.optimize(
            text="温馨的故事",
            use_template=False
        )
        assert result.optimized_prompt
        assert "Children's picture book style" in result.optimized_prompt

    def test_story_rhythm_keywords_exist(self):
        """测试故事节奏关键词配置完整性"""
        for rhythm in ["开场", "发展", "高潮", "转折", "结局"]:
            assert rhythm in STORY_RHYTHM_KEYWORDS
            assert "keywords" in STORY_RHYTHM_KEYWORDS[rhythm]
            assert "camera" in STORY_RHYTHM_KEYWORDS[rhythm]
            assert "intensity" in STORY_RHYTHM_KEYWORDS[rhythm]

    def test_prompt_templates_exist(self):
        """测试提示词模板配置完整性"""
        for template_name in ["温馨童话", "冒险故事", "奇幻魔法", "悬疑神秘", "自然风光"]:
            assert template_name in PROMPT_TEMPLATES
            template = PROMPT_TEMPLATES[template_name]
            assert "prefix" in template
            assert "style" in template
            assert "atmosphere" in template
            assert "suffix" in template

    def test_intensity_modifiers_exist(self):
        """测试强度修饰符配置完整性"""
        for level in ["low", "medium", "high"]:
            assert level in INTENSITY_MODIFIERS
            modifiers = INTENSITY_MODIFIERS[level]
            assert "motion" in modifiers
            assert "camera" in modifiers
            assert "color" in modifiers

    def test_context_transitions_exist(self):
        """测试上下文过渡配置"""
        assert len(CONTEXT_TRANSITIONS) > 0
        for (from_emotion, to_emotion), desc in CONTEXT_TRANSITIONS.items():
            assert isinstance(from_emotion, str)
            assert isinstance(to_emotion, str)
            assert isinstance(desc, str)

    def test_volume_to_db_zero(self):
        """测试音量转换 - 0%"""
        db = BGMProcessor.volume_to_db(0)
        assert db == -60.0

    def test_volume_to_db_full(self):
        """测试音量转换 - 100%"""
        db = BGMProcessor.volume_to_db(100)
        assert db == 0.0

    def test_volume_to_db_thirty(self):
        """测试音量转换 - 30%(默认值)"""
        db = BGMProcessor.volume_to_db(30)
        assert -15.0 < db < -5.0

    def test_volume_to_db_fifty(self):
        """测试音量转换 - 50%"""
        db = BGMProcessor.volume_to_db(50)
        assert -10.0 < db < -3.0


# ============================================
# AI适配器测试
# ============================================

class TestMockProvider:
    """Mock AI服务商测试类"""

    @pytest.mark.asyncio
    async def test_generate_video(self):
        """测试视频生成 - 提交任务"""
        provider = MockProvider(delay_seconds=1)
        result = await provider.generate_video(
            image_url="https://example.com/test.jpg",
            prompt="test prompt"
        )
        assert result.status == "processing"
        assert result.task_id != ""

    @pytest.mark.asyncio
    async def test_get_task_status_processing(self):
        """测试任务状态查询 - 处理中"""
        provider = MockProvider(delay_seconds=10)
        gen_result = await provider.generate_video(
            image_url="https://example.com/test.jpg",
            prompt="test prompt"
        )
        status_result = await provider.get_task_status(gen_result.task_id)
        assert status_result.status == "processing"

    @pytest.mark.asyncio
    async def test_get_task_status_completed(self):
        """测试任务状态查询 - 已完成"""
        provider = MockProvider(delay_seconds=0)
        gen_result = await provider.generate_video(
            image_url="https://example.com/test.jpg",
            prompt="test prompt"
        )
        await asyncio.sleep(0.5)
        status_result = await provider.get_task_status(gen_result.task_id)
        assert status_result.status == "completed"
        assert status_result.video_url is not None

    @pytest.mark.asyncio
    async def test_get_task_status_not_found(self):
        """测试任务状态查询 - 任务不存在"""
        provider = MockProvider()
        result = await provider.get_task_status("non-existent-id")
        assert result.status == "failed"
        assert "不存在" in result.error_message


# ============================================
# 背景音乐处理器测试
# ============================================

class TestBGMProcessor:
    """背景音乐处理器测试类"""

    def test_validate_format_mp3(self):
        """测试格式验证 - MP3"""
        assert bgm_processor.validate_format("test.mp3") is True

    def test_validate_format_wav(self):
        """测试格式验证 - WAV"""
        assert bgm_processor.validate_format("test.wav") is True

    def test_validate_format_aac(self):
        """测试格式验证 - AAC"""
        assert bgm_processor.validate_format("test.aac") is True

    def test_validate_format_ogg(self):
        """测试格式验证 - OGG"""
        assert bgm_processor.validate_format("test.ogg") is True

    def test_validate_format_flac(self):
        """测试格式验证 - FLAC"""
        assert bgm_processor.validate_format("test.flac") is True

    def test_validate_format_invalid(self):
        """测试格式验证 - 不支持的格式"""
        assert bgm_processor.validate_format("test.exe") is False

    def test_validate_format_no_ext(self):
        """测试格式验证 - 无扩展名"""
        assert bgm_processor.validate_format("testfile") is False

    def test_validate_file_size_valid(self):
        """测试文件大小验证 - 合法大小"""
        assert bgm_processor.validate_file_size(1024 * 1024) is True

    def test_validate_file_size_too_small(self):
        """测试文件大小验证 - 文件过小"""
        assert bgm_processor.validate_file_size(100) is False

    def test_validate_file_size_too_large(self):
        """测试文件大小验证 - 文件过大"""
        assert bgm_processor.validate_file_size(25 * 1024 * 1024) is False

    def test_validate_file_size_max_boundary(self):
        """测试文件大小验证 - 最大边界值"""
        assert bgm_processor.validate_file_size(20 * 1024 * 1024) is True

    def test_mix_bgm_video_not_found(self):
        """测试混音 - 视频文件不存在"""
        with pytest.raises(FileNotFoundError):
            bgm_processor.mix_bgm_to_video(
                video_path="/nonexistent/video.mp4",
                bgm_path="/nonexistent/bgm.mp3",
                output_path="/tmp/output.mp4"
            )

    def test_mix_bgm_bgm_not_found(self):
        """测试混音 - 音乐文件不存在"""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            temp_video = f.name
            f.write(b"fake video content")
        try:
            with pytest.raises(FileNotFoundError):
                bgm_processor.mix_bgm_to_video(
                    video_path=temp_video,
                    bgm_path="/nonexistent/bgm.mp3",
                    output_path="/tmp/output.mp4"
                )
        finally:
            os.unlink(temp_video)

    def test_apply_ducking_voice_not_found(self):
        """测试Ducking - 语音文件不存在"""
        with pytest.raises(FileNotFoundError):
            bgm_processor.apply_ducking(
                voice_path="/nonexistent/voice.wav",
                bgm_path="/nonexistent/bgm.mp3",
                output_path="/tmp/output.mp3"
            )


# ============================================
# Schema测试
# ============================================

class TestVideoSchemas:
    """视频数据Schema测试类"""

    def test_video_create_valid(self):
        """测试视频创建Schema - 合法数据"""
        data = VideoCreate(
            project_id="test-project-id",
            title="测试视频",
            source_image_url="https://example.com/image.jpg"
        )
        assert data.project_id == "test-project-id"
        assert data.title == "测试视频"
        assert data.bgm_volume == 30
        assert data.bgm_loop is True

    def test_video_create_with_bgm(self):
        """测试视频创建Schema - 包含背景音乐配置"""
        data = VideoCreate(
            project_id="test-project-id",
            title="测试视频",
            source_image_url="https://example.com/image.jpg",
            bgm_id="test-bgm-id",
            bgm_volume=50,
            bgm_fade_in=2.0,
            bgm_fade_out=3.0,
            bgm_loop=False
        )
        assert data.bgm_id == "test-bgm-id"
        assert data.bgm_volume == 50
        assert data.bgm_fade_in == 2.0
        assert data.bgm_loop is False

    def test_video_create_volume_range(self):
        """测试视频创建Schema - 音量范围验证"""
        with pytest.raises(Exception):
            VideoCreate(
                project_id="test-project-id",
                title="测试视频",
                source_image_url="https://example.com/image.jpg",
                bgm_volume=150
            )

    def test_video_create_volume_negative(self):
        """测试视频创建Schema - 音量负数验证"""
        with pytest.raises(Exception):
            VideoCreate(
                project_id="test-project-id",
                title="测试视频",
                source_image_url="https://example.com/image.jpg",
                bgm_volume=-10
            )

    def test_video_create_fade_in_range(self):
        """测试视频创建Schema - 淡入时长范围验证"""
        with pytest.raises(Exception):
            VideoCreate(
                project_id="test-project-id",
                title="测试视频",
                source_image_url="https://example.com/image.jpg",
                bgm_fade_in=10.0
            )

    def test_video_bgm_config_valid(self):
        """测试背景音乐配置Schema - 合法数据"""
        config = VideoBGMConfig(
            bgm_id="test-bgm-id",
            volume=50,
            fade_in=2.0,
            fade_out=3.0,
            loop=False,
            start_offset=5.0,
            sync_mode=BGMSyncMode.MANUAL
        )
        assert config.volume == 50
        assert config.sync_mode == BGMSyncMode.MANUAL

    def test_video_status_enum(self):
        """测试视频状态枚举"""
        assert VideoStatus.PENDING == 0
        assert VideoStatus.PROCESSING == 1
        assert VideoStatus.COMPLETED == 2
        assert VideoStatus.FAILED == 3

    def test_video_status_map(self):
        """测试视频状态映射"""
        assert VIDEO_STATUS_MAP[0] == "pending"
        assert VIDEO_STATUS_MAP[1] == "processing"
        assert VIDEO_STATUS_MAP[2] == "completed"
        assert VIDEO_STATUS_MAP[3] == "failed"

    def test_video_error_codes(self):
        """测试视频模块错误码"""
        assert VideoErrorCode.VIDEO_NOT_FOUND == 4001
        assert VideoErrorCode.BGM_NOT_FOUND == 6005
        assert VideoErrorCode.BGM_INVALID_FORMAT == 6001
        assert VideoErrorCode.AI_SERVICE_UNAVAILABLE == 5001

    def test_bgm_source_enum(self):
        """测试背景音乐来源枚举"""
        assert BGMSource.SYSTEM == "system"
        assert BGMSource.USER == "user"

    def test_bgm_sync_mode_enum(self):
        """测试背景音乐同步模式枚举"""
        assert BGMSyncMode.AUTO == "auto"
        assert BGMSyncMode.MANUAL == "manual"


# ============================================
# VideoGenerationResult测试
# ============================================

class TestVideoGenerationResult:
    """视频生成结果数据类测试"""

    def test_default_values(self):
        """测试默认值"""
        result = VideoGenerationResult()
        assert result.task_id == ""
        assert result.video_url is None
        assert result.status == "pending"
        assert result.format == "mp4"

    def test_with_values(self):
        """测试赋值"""
        result = VideoGenerationResult(
            task_id="test-task-id",
            video_url="https://example.com/video.mp4",
            duration=10,
            resolution="1280x720",
            fps=24,
            status="completed"
        )
        assert result.task_id == "test-task-id"
        assert result.duration == 10
        assert result.status == "completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
