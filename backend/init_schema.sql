-- ============================================
-- TaleVoice 数据库初始化脚本
-- 版本: v2.0
-- 日期: 2026-04-17
-- 数据库: PostgreSQL 15+
-- 说明: 完全基于 database_schema_design.md 文档定义
-- ============================================

-- 设置客户端编码
SET client_encoding = 'UTF8';

-- ============================================
-- 1. 用户表 (users)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT uk_users_username UNIQUE (username),
    CONSTRAINT uk_users_email UNIQUE (email)
);

COMMENT ON TABLE users IS '用户表 - 存储系统用户的基本信息，包括认证信息和个人资料';
COMMENT ON COLUMN users.id IS '用户唯一标识';
COMMENT ON COLUMN users.username IS '用户名';
COMMENT ON COLUMN users.email IS '邮箱地址';
COMMENT ON COLUMN users.password_hash IS '密码哈希值（bcrypt加密）';
COMMENT ON COLUMN users.avatar_url IS '头像URL';
COMMENT ON COLUMN users.created_at IS '创建时间';

-- ============================================
-- 2. 故事表 (stories) - 先创建不带 project_id 外键
-- ============================================
CREATE TABLE IF NOT EXISTS stories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    project_id UUID,
    
    CONSTRAINT fk_stories_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

COMMENT ON TABLE stories IS '故事表 - 存储用户创建的故事文本内容，包括标题、正文、分类等信息';
COMMENT ON COLUMN stories.id IS '故事唯一标识';
COMMENT ON COLUMN stories.user_id IS '创建者用户ID（外键 → users.id）';
COMMENT ON COLUMN stories.title IS '故事标题';
COMMENT ON COLUMN stories.content IS '故事正文内容';
COMMENT ON COLUMN stories.created_at IS '创建时间';
COMMENT ON COLUMN stories.updated_at IS '更新时间（自动更新）';
COMMENT ON COLUMN stories.project_id IS '关联的项目ID（外键 → projects.id）';

-- ============================================
-- 3. 项目表 (projects)
-- ============================================
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_projects_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_projects_story FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE SET NULL,
    CONSTRAINT chk_projects_type CHECK (project_type IN ('audio', 'video')),
    CONSTRAINT chk_projects_status CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

COMMENT ON TABLE projects IS '项目表 - 存储生成的音频或视频项目，包括文件信息、状态、生成参数等';
COMMENT ON COLUMN projects.id IS '项目唯一标识';
COMMENT ON COLUMN projects.user_id IS '创建者用户ID（外键 → users.id）';
COMMENT ON COLUMN projects.story_id IS '关联的故事ID（外键 → stories.id）';
COMMENT ON COLUMN projects.title IS '项目标题';
COMMENT ON COLUMN projects.description IS '项目详细描述内容';
COMMENT ON COLUMN projects.project_type IS '项目类型: audio/video';
COMMENT ON COLUMN projects.style IS '项目风格';
COMMENT ON COLUMN projects.file_url IS '项目文件URL';
COMMENT ON COLUMN projects.thumbnail_url IS '缩略图URL';
COMMENT ON COLUMN projects.duration IS '项目时长（秒）';
COMMENT ON COLUMN projects.status IS '状态: pending/processing/completed/failed';
COMMENT ON COLUMN projects.created_at IS '创建时间';
COMMENT ON COLUMN projects.updated_at IS '更新时间（自动更新）';

-- ============================================
-- 添加 stories 表的 project_id 外键约束
-- ============================================
ALTER TABLE stories 
ADD CONSTRAINT fk_stories_project 
FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL;

-- ============================================
-- 4. 声音模型表 (voice_models)
-- ============================================
CREATE TABLE IF NOT EXISTS voice_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    model_url VARCHAR(500),
    sample_url VARCHAR(500),
    sample_duration INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'training',
    similarity FLOAT NOT NULL DEFAULT 0.8,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_voice_models_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_voice_models_status CHECK (status IN ('training', 'ready', 'failed')),
    CONSTRAINT chk_voice_models_similarity CHECK (similarity >= 0 AND similarity <= 1)
);

COMMENT ON TABLE voice_models IS '声音模型表 - 存储用户的个性化声音模型信息，包括模型文件、训练状态等';
COMMENT ON COLUMN voice_models.id IS '模型唯一标识';
COMMENT ON COLUMN voice_models.user_id IS '所有者用户ID（外键 → users.id）';
COMMENT ON COLUMN voice_models.name IS '模型名称';
COMMENT ON COLUMN voice_models.model_url IS '模型文件URL';
COMMENT ON COLUMN voice_models.sample_url IS '样本音频URL';
COMMENT ON COLUMN voice_models.sample_duration IS '样本音频时长（秒）';
COMMENT ON COLUMN voice_models.status IS '状态: training/ready/failed';
COMMENT ON COLUMN voice_models.similarity IS '声音相似度（0-1）';
COMMENT ON COLUMN voice_models.created_at IS '创建时间';
COMMENT ON COLUMN voice_models.updated_at IS '更新时间（自动更新）';

-- ============================================
-- 5. 音频表 (audio_files)
-- ============================================
CREATE TABLE IF NOT EXISTS audio_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    file_url VARCHAR(500),
    title VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    project_id UUID,
    
    CONSTRAINT fk_audio_files_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_audio_files_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
);

COMMENT ON TABLE audio_files IS '音频表 - 存储用户的个性化音频信息，包括音频文件、训练状态等';
COMMENT ON COLUMN audio_files.id IS '音频唯一标识';
COMMENT ON COLUMN audio_files.user_id IS '所有者用户ID（外键 → users.id）';
COMMENT ON COLUMN audio_files.name IS '音频名称';
COMMENT ON COLUMN audio_files.file_url IS '音频文件URL';
COMMENT ON COLUMN audio_files.title IS '音频标题';
COMMENT ON COLUMN audio_files.created_at IS '创建时间';
COMMENT ON COLUMN audio_files.updated_at IS '更新时间（自动更新）';
COMMENT ON COLUMN audio_files.project_id IS '关联的项目ID（外键 → projects.id）';

-- ============================================
-- 索引创建
-- ============================================

-- ============================================
-- 1. 用户表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

-- ============================================
-- 2. 故事表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_stories_user_id ON stories(user_id);
CREATE INDEX IF NOT EXISTS idx_stories_project_id ON stories(project_id);
CREATE INDEX IF NOT EXISTS idx_stories_created_at ON stories(created_at DESC);

-- ============================================
-- 3. 项目表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_story_id ON projects(story_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_type ON projects(project_type);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at DESC);

-- ============================================
-- 4. 声音模型表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_voice_models_user_id ON voice_models(user_id);
CREATE INDEX IF NOT EXISTS idx_voice_models_status ON voice_models(status);
CREATE INDEX IF NOT EXISTS idx_voice_models_created_at ON voice_models(created_at DESC);

-- ============================================
-- 5. 音频表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_audio_files_user_id ON audio_files(user_id);
CREATE INDEX IF NOT EXISTS idx_audio_files_project_id ON audio_files(project_id);
CREATE INDEX IF NOT EXISTS idx_audio_files_created_at ON audio_files(created_at DESC);

-- ============================================
-- updated_at 自动更新触发器
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- stories 表触发器
CREATE TRIGGER trigger_stories_update_updated_at
    BEFORE UPDATE ON stories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- projects 表触发器
CREATE TRIGGER trigger_projects_update_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- voice_models 表触发器
CREATE TRIGGER trigger_voice_models_update_updated_at
    BEFORE UPDATE ON voice_models
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- audio_files 表触发器
CREATE TRIGGER trigger_audio_files_update_updated_at
    BEFORE UPDATE ON audio_files
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 初始化完成
-- ============================================
