-- ============================================
-- TaleVoice 数据库初始化脚本
-- 版本: v3.0
-- 日期: 2026-04-24
-- 数据库: PostgreSQL 15+
-- 说明: 完全基于 database_schema_design.md 文档定义
-- 新增: t_bgm、t_subtitle、t_subtitle_segment、t_edit_task、t_edit_clip 五张表
-- 表名约定: 使用 t_ 前缀，如 t_user、t_project、t_video 等
-- ============================================

-- 设置客户端编码
SET client_encoding = 'UTF8';

-- ============================================
-- 1. 用户表 (t_user)
-- ============================================
CREATE TABLE IF NOT EXISTS t_user (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    create_time TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT uk_t_user_username UNIQUE (username),
    CONSTRAINT uk_t_user_email UNIQUE (email)
);

COMMENT ON TABLE t_user IS '用户表 - 存储系统用户的基本信息，包括认证信息和个人资料';
COMMENT ON COLUMN t_user.user_id IS '用户唯一标识';
COMMENT ON COLUMN t_user.username IS '用户名';
COMMENT ON COLUMN t_user.email IS '邮箱地址';
COMMENT ON COLUMN t_user.password_hash IS '密码哈希值（bcrypt加密）';
COMMENT ON COLUMN t_user.avatar_url IS '头像URL';
COMMENT ON COLUMN t_user.create_time IS '创建时间';

-- ============================================
-- 2. 故事表 (t_story) - 先创建不带 project_id 外键
-- ============================================
CREATE TABLE IF NOT EXISTS t_story (
    story_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    create_time TIMESTAMP NOT NULL DEFAULT NOW(),
    update_time TIMESTAMP NOT NULL DEFAULT NOW(),
    project_id UUID,
    
    CONSTRAINT fk_t_story_user FOREIGN KEY (user_id) REFERENCES t_user(user_id) ON DELETE CASCADE
);

COMMENT ON TABLE t_story IS '故事表 - 存储用户创建的故事文本内容，包括标题、正文、分类等信息';
COMMENT ON COLUMN t_story.story_id IS '故事唯一标识';
COMMENT ON COLUMN t_story.user_id IS '创建者用户ID（外键 → t_user.user_id）';
COMMENT ON COLUMN t_story.title IS '故事标题';
COMMENT ON COLUMN t_story.content IS '故事正文内容';
COMMENT ON COLUMN t_story.create_time IS '创建时间';
COMMENT ON COLUMN t_story.update_time IS '更新时间（自动更新）';
COMMENT ON COLUMN t_story.project_id IS '关联的项目ID（外键 → t_project.project_id）';

-- ============================================
-- 3. 项目表 (t_project)
-- ============================================
CREATE TABLE IF NOT EXISTS t_project (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    story_id UUID,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    project_type VARCHAR(20) NOT NULL,
    style VARCHAR(100) DEFAULT 'default',
    file_url VARCHAR(500),
    thumbnail_url VARCHAR(500),
    duration INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'processing',
    create_time TIMESTAMP NOT NULL DEFAULT NOW(),
    update_time TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_t_project_user FOREIGN KEY (user_id) REFERENCES t_user(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_t_project_story FOREIGN KEY (story_id) REFERENCES t_story(story_id) ON DELETE SET NULL,
    CONSTRAINT chk_t_project_type CHECK (project_type IN ('audio', 'video')),
    CONSTRAINT chk_t_project_status CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

COMMENT ON TABLE t_project IS '项目表 - 存储生成的音频或视频项目，包括文件信息、状态、生成参数等';
COMMENT ON COLUMN t_project.project_id IS '项目唯一标识';
COMMENT ON COLUMN t_project.user_id IS '创建者用户ID（外键 → t_user.user_id）';
COMMENT ON COLUMN t_project.story_id IS '关联的故事ID（外键 → t_story.story_id）';
COMMENT ON COLUMN t_project.title IS '项目标题';
COMMENT ON COLUMN t_project.description IS '项目详细描述内容';
COMMENT ON COLUMN t_project.project_type IS '项目类型: audio/video';
COMMENT ON COLUMN t_project.style IS '项目风格';
COMMENT ON COLUMN t_project.file_url IS '项目文件URL';
COMMENT ON COLUMN t_project.thumbnail_url IS '缩略图URL';
COMMENT ON COLUMN t_project.duration IS '项目时长（秒）';
COMMENT ON COLUMN t_project.status IS '状态: pending/processing/completed/failed';
COMMENT ON COLUMN t_project.create_time IS '创建时间';
COMMENT ON COLUMN t_project.update_time IS '更新时间（自动更新）';

-- ============================================
-- 添加 t_story 表的 project_id 外键约束
-- ============================================
ALTER TABLE t_story 
ADD CONSTRAINT fk_t_story_project 
FOREIGN KEY (project_id) REFERENCES t_project(project_id) ON DELETE SET NULL;

-- ============================================
-- 4. 声音模型表 (t_voice_sample)
-- ============================================
CREATE TABLE IF NOT EXISTS t_voice_sample (
    voice_sample_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    model_url VARCHAR(500),
    sample_url VARCHAR(500),
    sample_duration INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'training',
    similarity FLOAT NOT NULL DEFAULT 0.8,
    create_time TIMESTAMP NOT NULL DEFAULT NOW(),
    update_time TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_t_voice_sample_user FOREIGN KEY (user_id) REFERENCES t_user(user_id) ON DELETE CASCADE,
    CONSTRAINT chk_t_voice_sample_status CHECK (status IN ('training', 'ready', 'failed')),
    CONSTRAINT chk_t_voice_sample_similarity CHECK (similarity >= 0 AND similarity <= 1)
);

COMMENT ON TABLE t_voice_sample IS '声音模型表 - 存储用户的个性化声音模型信息，包括模型文件、训练状态等';
COMMENT ON COLUMN t_voice_sample.voice_sample_id IS '模型唯一标识';
COMMENT ON COLUMN t_voice_sample.user_id IS '所有者用户ID（外键 → t_user.user_id）';
COMMENT ON COLUMN t_voice_sample.name IS '模型名称';
COMMENT ON COLUMN t_voice_sample.model_url IS '模型文件URL';
COMMENT ON COLUMN t_voice_sample.sample_url IS '样本音频URL';
COMMENT ON COLUMN t_voice_sample.sample_duration IS '样本音频时长（秒）';
COMMENT ON COLUMN t_voice_sample.status IS '状态: training/ready/failed';
COMMENT ON COLUMN t_voice_sample.similarity IS '声音相似度（0-1）';
COMMENT ON COLUMN t_voice_sample.create_time IS '创建时间';
COMMENT ON COLUMN t_voice_sample.update_time IS '更新时间（自动更新）';

-- ============================================
-- 5. 音频表 (t_audio)
-- ============================================
CREATE TABLE IF NOT EXISTS t_audio (
    audio_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    file_url VARCHAR(500),
    title VARCHAR(100) NOT NULL,
    create_time TIMESTAMP NOT NULL DEFAULT NOW(),
    update_time TIMESTAMP NOT NULL DEFAULT NOW(),
    project_id UUID,
    
    CONSTRAINT fk_t_audio_user FOREIGN KEY (user_id) REFERENCES t_user(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_t_audio_project FOREIGN KEY (project_id) REFERENCES t_project(project_id) ON DELETE SET NULL
);

COMMENT ON TABLE t_audio IS '音频表 - 存储用户的个性化音频信息，包括音频文件、训练状态等';
COMMENT ON COLUMN t_audio.audio_id IS '音频唯一标识';
COMMENT ON COLUMN t_audio.user_id IS '所有者用户ID（外键 → t_user.user_id）';
COMMENT ON COLUMN t_audio.name IS '音频名称';
COMMENT ON COLUMN t_audio.file_url IS '音频文件URL';
COMMENT ON COLUMN t_audio.title IS '音频标题';
COMMENT ON COLUMN t_audio.create_time IS '创建时间';
COMMENT ON COLUMN t_audio.update_time IS '更新时间（自动更新）';
COMMENT ON COLUMN t_audio.project_id IS '关联的项目ID（外键 → t_project.project_id）';

-- ============================================
-- 6. 视频表 (t_video)
-- ============================================
CREATE TABLE IF NOT EXISTS t_video (
    video_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    user_id UUID NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    source_image_url VARCHAR(500),
    file_url VARCHAR(500),
    thumbnail_url VARCHAR(500),
    duration INTEGER,
    resolution VARCHAR(20),
    fps INTEGER,
    file_size BIGINT,
    format VARCHAR(20) DEFAULT 'mp4',
    prompt TEXT,
    bgm_id UUID,
    bgm_volume INTEGER DEFAULT 30,
    bgm_fade_in VARCHAR(16) DEFAULT '1.0',
    bgm_fade_out VARCHAR(16) DEFAULT '1.5',
    bgm_loop INTEGER DEFAULT 1,
    create_time TIMESTAMP NOT NULL DEFAULT NOW(),
    update_time TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_t_video_project FOREIGN KEY (project_id) REFERENCES t_project(project_id) ON DELETE CASCADE,
    CONSTRAINT fk_t_video_user FOREIGN KEY (user_id) REFERENCES t_user(user_id) ON DELETE CASCADE,
    CONSTRAINT chk_t_video_bgm_volume CHECK (bgm_volume >= 0 AND bgm_volume <= 100)
);

COMMENT ON TABLE t_video IS '视频表 - 存储由图片通过大模型生成的视频信息，包括源图片、生成的视频文件、视频属性、背景音乐配置等';
COMMENT ON COLUMN t_video.video_id IS '视频唯一标识';
COMMENT ON COLUMN t_video.project_id IS '关联的项目ID（外键 → t_project.project_id）';
COMMENT ON COLUMN t_video.user_id IS '所有者用户ID（外键 → t_user.user_id）';
COMMENT ON COLUMN t_video.title IS '视频标题';
COMMENT ON COLUMN t_video.description IS '视频描述';
COMMENT ON COLUMN t_video.source_image_url IS '源图片URL（生成视频的原始图片）';
COMMENT ON COLUMN t_video.file_url IS '视频文件URL';
COMMENT ON COLUMN t_video.thumbnail_url IS '缩略图URL';
COMMENT ON COLUMN t_video.duration IS '视频时长（秒）';
COMMENT ON COLUMN t_video.resolution IS '视频分辨率（如 1920x1080）';
COMMENT ON COLUMN t_video.fps IS '帧率（每秒帧数）';
COMMENT ON COLUMN t_video.file_size IS '文件大小（字节）';
COMMENT ON COLUMN t_video.format IS '视频格式';
COMMENT ON COLUMN t_video.prompt IS 'AI生成提示词';
COMMENT ON COLUMN t_video.bgm_id IS '关联的背景音乐ID（外键 → t_bgm.bgm_id）';
COMMENT ON COLUMN t_video.bgm_volume IS '背景音乐音量（0-100）';
COMMENT ON COLUMN t_video.bgm_fade_in IS '背景音乐淡入时长（秒）';
COMMENT ON COLUMN t_video.bgm_fade_out IS '背景音乐淡出时长（秒）';
COMMENT ON COLUMN t_video.bgm_loop IS '背景音乐是否循环（0否/1是）';
COMMENT ON COLUMN t_video.create_time IS '创建时间';
COMMENT ON COLUMN t_video.update_time IS '更新时间（自动更新）';

-- ============================================
-- 7. 背景音乐表 (t_bgm)
-- ============================================
CREATE TABLE IF NOT EXISTS t_bgm (
    bgm_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(256) NOT NULL,
    user_id UUID,
    source VARCHAR(32) DEFAULT 'system',
    style VARCHAR(128),
    emotion VARCHAR(64),
    file_url VARCHAR(512),
    sample_url VARCHAR(512),
    duration INTEGER,
    bpm INTEGER,
    format VARCHAR(32) DEFAULT 'mp3',
    sample_rate INTEGER,
    channels INTEGER,
    bit_rate INTEGER,
    file_size BIGINT,
    play_count INTEGER DEFAULT 0,
    create_time TIMESTAMP NOT NULL DEFAULT NOW(),
    update_time TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_t_bgm_user FOREIGN KEY (user_id) REFERENCES t_user(user_id) ON DELETE SET NULL,
    CONSTRAINT chk_t_bgm_source CHECK (source IN ('system', 'user', 'third_party'))
);

COMMENT ON TABLE t_bgm IS '背景音乐表 - 存储系统预置和用户上传的背景音乐资源信息';
COMMENT ON COLUMN t_bgm.bgm_id IS '背景音乐唯一标识';
COMMENT ON COLUMN t_bgm.name IS '音乐名称';
COMMENT ON COLUMN t_bgm.user_id IS '上传用户ID（系统预置为NULL）';
COMMENT ON COLUMN t_bgm.source IS '来源类型: system(系统预置)/user(用户上传)/third_party(第三方)';
COMMENT ON COLUMN t_bgm.style IS '音乐风格（如：轻快、舒缓、激昂等）';
COMMENT ON COLUMN t_bgm.emotion IS '情感标签（如：温馨、欢快、悲伤等）';
COMMENT ON COLUMN t_bgm.file_url IS '音乐文件URL';
COMMENT ON COLUMN t_bgm.sample_url IS '试听片段URL';
COMMENT ON COLUMN t_bgm.duration IS '音乐时长（秒）';
COMMENT ON COLUMN t_bgm.bpm IS '节奏BPM（每分钟节拍数）';
COMMENT ON COLUMN t_bgm.format IS '音频格式（mp3/wav/aac等）';
COMMENT ON COLUMN t_bgm.sample_rate IS '采样率（Hz）';
COMMENT ON COLUMN t_bgm.channels IS '声道数';
COMMENT ON COLUMN t_bgm.bit_rate IS '比特率（kbps）';
COMMENT ON COLUMN t_bgm.file_size IS '文件大小（字节）';
COMMENT ON COLUMN t_bgm.play_count IS '播放次数';
COMMENT ON COLUMN t_bgm.create_time IS '创建时间';
COMMENT ON COLUMN t_bgm.update_time IS '更新时间（自动更新）';

-- ============================================
-- 8. 字幕表 (t_subtitle)
-- ============================================
CREATE TABLE IF NOT EXISTS t_subtitle (
    subtitle_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL,
    user_id UUID NOT NULL,
    title VARCHAR(256),
    language VARCHAR(16) DEFAULT 'zh-CN',
    format VARCHAR(10) DEFAULT 'srt',
    content TEXT,
    file_url VARCHAR(512),
    task_id VARCHAR(128),
    status VARCHAR(20) DEFAULT 'pending',
    confidence FLOAT,
    create_time TIMESTAMP NOT NULL DEFAULT NOW(),
    update_time TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_t_subtitle_video FOREIGN KEY (video_id) REFERENCES t_video(video_id) ON DELETE CASCADE,
    CONSTRAINT fk_t_subtitle_user FOREIGN KEY (user_id) REFERENCES t_user(user_id) ON DELETE CASCADE,
    CONSTRAINT chk_t_subtitle_format CHECK (format IN ('srt', 'ass', 'vtt', 'json')),
    CONSTRAINT chk_t_subtitle_status CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

COMMENT ON TABLE t_subtitle IS '字幕表 - 存储视频字幕生成任务和结果信息';
COMMENT ON COLUMN t_subtitle.subtitle_id IS '字幕唯一标识';
COMMENT ON COLUMN t_subtitle.video_id IS '关联视频ID（外键 → t_video.video_id）';
COMMENT ON COLUMN t_subtitle.user_id IS '创建用户ID（外键 → t_user.user_id）';
COMMENT ON COLUMN t_subtitle.title IS '字幕标题';
COMMENT ON COLUMN t_subtitle.language IS '语言代码（zh-CN/en-US等）';
COMMENT ON COLUMN t_subtitle.format IS '字幕格式: srt/ass/vtt/json';
COMMENT ON COLUMN t_subtitle.content IS '字幕内容文本';
COMMENT ON COLUMN t_subtitle.file_url IS '字幕文件URL';
COMMENT ON COLUMN t_subtitle.task_id IS '阿里云字幕生成任务ID';
COMMENT ON COLUMN t_subtitle.status IS '任务状态: pending/processing/completed/failed';
COMMENT ON COLUMN t_subtitle.confidence IS '整体识别置信度（0-1）';
COMMENT ON COLUMN t_subtitle.create_time IS '创建时间';
COMMENT ON COLUMN t_subtitle.update_time IS '更新时间（自动更新）';

-- ============================================
-- 9. 字幕片段表 (t_subtitle_segment)
-- ============================================
CREATE TABLE IF NOT EXISTS t_subtitle_segment (
    segment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subtitle_id UUID NOT NULL,
    segment_index INTEGER NOT NULL,
    start_time BIGINT NOT NULL,
    end_time BIGINT NOT NULL,
    text TEXT NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    create_time TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_t_subtitle_segment_subtitle FOREIGN KEY (subtitle_id) REFERENCES t_subtitle(subtitle_id) ON DELETE CASCADE,
    CONSTRAINT chk_t_subtitle_segment_time CHECK (start_time >= 0 AND end_time >= start_time),
    CONSTRAINT chk_t_subtitle_segment_confidence CHECK (confidence >= 0 AND confidence <= 1)
);

COMMENT ON TABLE t_subtitle_segment IS '字幕片段表 - 存储字幕的具体时间片段和文本内容';
COMMENT ON COLUMN t_subtitle_segment.segment_id IS '片段唯一标识';
COMMENT ON COLUMN t_subtitle_segment.subtitle_id IS '关联字幕ID（外键 → t_subtitle.subtitle_id）';
COMMENT ON COLUMN t_subtitle_segment.segment_index IS '片段序号（从1开始）';
COMMENT ON COLUMN t_subtitle_segment.start_time IS '开始时间（毫秒）';
COMMENT ON COLUMN t_subtitle_segment.end_time IS '结束时间（毫秒）';
COMMENT ON COLUMN t_subtitle_segment.text IS '字幕文本内容';
COMMENT ON COLUMN t_subtitle_segment.confidence IS '片段识别置信度（0-1）';
COMMENT ON COLUMN t_subtitle_segment.create_time IS '创建时间';

-- ============================================
-- 10. 剪辑任务表 (t_edit_task)
-- ============================================
CREATE TABLE IF NOT EXISTS t_edit_task (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    user_id UUID NOT NULL,
    title VARCHAR(256) NOT NULL,
    description TEXT,
    timeline_config JSONB,
    output_url VARCHAR(512),
    output_duration INTEGER,
    resolution VARCHAR(20) DEFAULT '1920x1080',
    fps INTEGER DEFAULT 30,
    aliyun_task_id VARCHAR(128),
    status VARCHAR(20) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    error_message TEXT,
    create_time TIMESTAMP NOT NULL DEFAULT NOW(),
    update_time TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_t_edit_task_project FOREIGN KEY (project_id) REFERENCES t_project(project_id) ON DELETE CASCADE,
    CONSTRAINT fk_t_edit_task_user FOREIGN KEY (user_id) REFERENCES t_user(user_id) ON DELETE CASCADE,
    CONSTRAINT chk_t_edit_task_status CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    CONSTRAINT chk_t_edit_task_progress CHECK (progress >= 0 AND progress <= 100)
);

COMMENT ON TABLE t_edit_task IS '剪辑任务表 - 存储视频智能剪辑任务信息和结果';
COMMENT ON COLUMN t_edit_task.task_id IS '剪辑任务唯一标识';
COMMENT ON COLUMN t_edit_task.project_id IS '关联项目ID（外键 → t_project.project_id）';
COMMENT ON COLUMN t_edit_task.user_id IS '创建用户ID（外键 → t_user.user_id）';
COMMENT ON COLUMN t_edit_task.title IS '任务标题';
COMMENT ON COLUMN t_edit_task.description IS '任务描述';
COMMENT ON COLUMN t_edit_task.timeline_config IS '时间线配置（JSON格式，包含片段、转场、滤镜、BGM等配置）';
COMMENT ON COLUMN t_edit_task.output_url IS '输出视频URL';
COMMENT ON COLUMN t_edit_task.output_duration IS '输出视频时长（秒）';
COMMENT ON COLUMN t_edit_task.resolution IS '输出分辨率';
COMMENT ON COLUMN t_edit_task.fps IS '输出帧率';
COMMENT ON COLUMN t_edit_task.aliyun_task_id IS '阿里云剪辑任务ID';
COMMENT ON COLUMN t_edit_task.status IS '任务状态: pending/processing/completed/failed';
COMMENT ON COLUMN t_edit_task.progress IS '任务进度（0-100）';
COMMENT ON COLUMN t_edit_task.error_message IS '错误信息';
COMMENT ON COLUMN t_edit_task.create_time IS '创建时间';
COMMENT ON COLUMN t_edit_task.update_time IS '更新时间（自动更新）';

-- ============================================
-- 11. 剪辑片段表 (t_edit_clip)
-- ============================================
CREATE TABLE IF NOT EXISTS t_edit_clip (
    clip_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL,
    video_id UUID,
    video_url VARCHAR(512) NOT NULL,
    clip_order INTEGER NOT NULL,
    start_time FLOAT DEFAULT 0,
    end_time FLOAT DEFAULT 0,
    duration FLOAT DEFAULT 0,
    transition_in VARCHAR(32) DEFAULT 'fade',
    transition_out VARCHAR(32) DEFAULT 'fade',
    transition_duration FLOAT DEFAULT 0.5,
    filter_type VARCHAR(32) DEFAULT 'none',
    volume INTEGER DEFAULT 100,
    create_time TIMESTAMP NOT NULL DEFAULT NOW(),
    update_time TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_t_edit_clip_task FOREIGN KEY (task_id) REFERENCES t_edit_task(task_id) ON DELETE CASCADE,
    CONSTRAINT fk_t_edit_clip_video FOREIGN KEY (video_id) REFERENCES t_video(video_id) ON DELETE SET NULL,
    CONSTRAINT chk_t_edit_clip_volume CHECK (volume >= 0 AND volume <= 100),
    CONSTRAINT chk_t_edit_clip_transition CHECK (transition_in IN ('fade', 'dissolve', 'wipe_left', 'wipe_right', 'wipe_up', 'wipe_down', 'slide_left', 'slide_right', 'zoom_in', 'zoom_out', 'rotate', 'blur', 'none')),
    CONSTRAINT chk_t_edit_clip_filter CHECK (filter_type IN ('none', 'warm', 'cool', 'vintage', 'black_white', 'sepia', 'bright', 'contrast', 'saturate', 'sharpen'))
);

COMMENT ON TABLE t_edit_clip IS '剪辑片段表 - 存储剪辑任务中各视频片段的详细配置';
COMMENT ON COLUMN t_edit_clip.clip_id IS '片段唯一标识';
COMMENT ON COLUMN t_edit_clip.task_id IS '关联剪辑任务ID（外键 → t_edit_task.task_id）';
COMMENT ON COLUMN t_edit_clip.video_id IS '关联视频ID（外键 → t_video.video_id）';
COMMENT ON COLUMN t_edit_clip.video_url IS '视频文件URL';
COMMENT ON COLUMN t_edit_clip.clip_order IS '片段顺序（从1开始）';
COMMENT ON COLUMN t_edit_clip.start_time IS '片段开始时间（秒）';
COMMENT ON COLUMN t_edit_clip.end_time IS '片段结束时间（秒）';
COMMENT ON COLUMN t_edit_clip.duration IS '片段时长（秒）';
COMMENT ON COLUMN t_edit_clip.transition_in IS '入场转场效果';
COMMENT ON COLUMN t_edit_clip.transition_out IS '出场转场效果';
COMMENT ON COLUMN t_edit_clip.transition_duration IS '转场时长（秒）';
COMMENT ON COLUMN t_edit_clip.filter_type IS '滤镜类型';
COMMENT ON COLUMN t_edit_clip.volume IS '音量（0-100）';
COMMENT ON COLUMN t_edit_clip.create_time IS '创建时间';
COMMENT ON COLUMN t_edit_clip.update_time IS '更新时间（自动更新）';

-- ============================================
-- 添加 t_video 表的 bgm_id 外键约束
-- ============================================
ALTER TABLE t_video 
ADD CONSTRAINT fk_t_video_bgm 
FOREIGN KEY (bgm_id) REFERENCES t_bgm(bgm_id) ON DELETE SET NULL;

-- ============================================
-- 索引创建
-- ============================================

-- ============================================
-- 1. 用户表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_t_user_email ON t_user(email);
CREATE INDEX IF NOT EXISTS idx_t_user_create_time ON t_user(create_time DESC);

-- ============================================
-- 2. 故事表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_t_story_user_id ON t_story(user_id);
CREATE INDEX IF NOT EXISTS idx_t_story_project_id ON t_story(project_id);
CREATE INDEX IF NOT EXISTS idx_t_story_create_time ON t_story(create_time DESC);

-- ============================================
-- 3. 项目表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_t_project_user_id ON t_project(user_id);
CREATE INDEX IF NOT EXISTS idx_t_project_story_id ON t_project(story_id);
CREATE INDEX IF NOT EXISTS idx_t_project_status ON t_project(status);
CREATE INDEX IF NOT EXISTS idx_t_project_type ON t_project(project_type);
CREATE INDEX IF NOT EXISTS idx_t_project_create_time ON t_project(create_time DESC);

-- ============================================
-- 4. 声音模型表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_t_voice_sample_user_id ON t_voice_sample(user_id);
CREATE INDEX IF NOT EXISTS idx_t_voice_sample_status ON t_voice_sample(status);
CREATE INDEX IF NOT EXISTS idx_t_voice_sample_create_time ON t_voice_sample(create_time DESC);

-- ============================================
-- 5. 音频表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_t_audio_user_id ON t_audio(user_id);
CREATE INDEX IF NOT EXISTS idx_t_audio_project_id ON t_audio(project_id);
CREATE INDEX IF NOT EXISTS idx_t_audio_create_time ON t_audio(create_time DESC);

-- ============================================
-- 6. 视频表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_t_video_project_id ON t_video(project_id);
CREATE INDEX IF NOT EXISTS idx_t_video_user_id ON t_video(user_id);
CREATE INDEX IF NOT EXISTS idx_t_video_bgm_id ON t_video(bgm_id);
CREATE INDEX IF NOT EXISTS idx_t_video_create_time ON t_video(create_time DESC);

-- ============================================
-- 7. 背景音乐表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_t_bgm_user_id ON t_bgm(user_id);
CREATE INDEX IF NOT EXISTS idx_t_bgm_source ON t_bgm(source);
CREATE INDEX IF NOT EXISTS idx_t_bgm_emotion ON t_bgm(emotion);
CREATE INDEX IF NOT EXISTS idx_t_bgm_style ON t_bgm(style);
CREATE INDEX IF NOT EXISTS idx_t_bgm_play_count ON t_bgm(play_count DESC);
CREATE INDEX IF NOT EXISTS idx_t_bgm_create_time ON t_bgm(create_time DESC);

-- ============================================
-- 8. 字幕表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_t_subtitle_video_id ON t_subtitle(video_id);
CREATE INDEX IF NOT EXISTS idx_t_subtitle_user_id ON t_subtitle(user_id);
CREATE INDEX IF NOT EXISTS idx_t_subtitle_status ON t_subtitle(status);
CREATE INDEX IF NOT EXISTS idx_t_subtitle_language ON t_subtitle(language);
CREATE INDEX IF NOT EXISTS idx_t_subtitle_task_id ON t_subtitle(task_id);
CREATE INDEX IF NOT EXISTS idx_t_subtitle_create_time ON t_subtitle(create_time DESC);

-- ============================================
-- 9. 字幕片段表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_t_subtitle_segment_subtitle_id ON t_subtitle_segment(subtitle_id);
CREATE INDEX IF NOT EXISTS idx_t_subtitle_segment_index ON t_subtitle_segment(subtitle_id, segment_index);

-- ============================================
-- 10. 剪辑任务表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_t_edit_task_project_id ON t_edit_task(project_id);
CREATE INDEX IF NOT EXISTS idx_t_edit_task_user_id ON t_edit_task(user_id);
CREATE INDEX IF NOT EXISTS idx_t_edit_task_status ON t_edit_task(status);
CREATE INDEX IF NOT EXISTS idx_t_edit_task_aliyun_task_id ON t_edit_task(aliyun_task_id);
CREATE INDEX IF NOT EXISTS idx_t_edit_task_create_time ON t_edit_task(create_time DESC);

-- ============================================
-- 11. 剪辑片段表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_t_edit_clip_task_id ON t_edit_clip(task_id);
CREATE INDEX IF NOT EXISTS idx_t_edit_clip_video_id ON t_edit_clip(video_id);
CREATE INDEX IF NOT EXISTS idx_t_edit_clip_order ON t_edit_clip(task_id, clip_order);

-- ============================================
-- update_time 自动更新触发器
-- ============================================

CREATE OR REPLACE FUNCTION update_update_time_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.update_time = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- t_story 表触发器
CREATE TRIGGER trigger_t_story_update_update_time
    BEFORE UPDATE ON t_story
    FOR EACH ROW
    EXECUTE FUNCTION update_update_time_column();

-- t_project 表触发器
CREATE TRIGGER trigger_t_project_update_update_time
    BEFORE UPDATE ON t_project
    FOR EACH ROW
    EXECUTE FUNCTION update_update_time_column();

-- t_voice_sample 表触发器
CREATE TRIGGER trigger_t_voice_sample_update_update_time
    BEFORE UPDATE ON t_voice_sample
    FOR EACH ROW
    EXECUTE FUNCTION update_update_time_column();

-- t_audio 表触发器
CREATE TRIGGER trigger_t_audio_update_update_time
    BEFORE UPDATE ON t_audio
    FOR EACH ROW
    EXECUTE FUNCTION update_update_time_column();

-- t_video 表触发器
CREATE TRIGGER trigger_t_video_update_update_time
    BEFORE UPDATE ON t_video
    FOR EACH ROW
    EXECUTE FUNCTION update_update_time_column();

-- t_bgm 表触发器
CREATE TRIGGER trigger_t_bgm_update_update_time
    BEFORE UPDATE ON t_bgm
    FOR EACH ROW
    EXECUTE FUNCTION update_update_time_column();

-- t_subtitle 表触发器
CREATE TRIGGER trigger_t_subtitle_update_update_time
    BEFORE UPDATE ON t_subtitle
    FOR EACH ROW
    EXECUTE FUNCTION update_update_time_column();

-- t_edit_task 表触发器
CREATE TRIGGER trigger_t_edit_task_update_update_time
    BEFORE UPDATE ON t_edit_task
    FOR EACH ROW
    EXECUTE FUNCTION update_update_time_column();

-- t_edit_clip 表触发器
CREATE TRIGGER trigger_t_edit_clip_update_update_time
    BEFORE UPDATE ON t_edit_clip
    FOR EACH ROW
    EXECUTE FUNCTION update_update_time_column();

-- ============================================
-- 初始化完成
-- ============================================
