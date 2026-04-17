-- ============================================
-- TaleVoice 数据库初始化脚本
-- 版本: v1.0
-- 日期: 2026-04-15
-- 数据库: PostgreSQL 15+
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
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT uk_users_username UNIQUE (username),
    CONSTRAINT uk_users_email UNIQUE (email),
    CONSTRAINT uk_users_phone UNIQUE (phone),
    CONSTRAINT chk_users_role CHECK (role IN ('user', 'admin', 'superadmin'))
);

COMMENT ON TABLE users IS '用户表 - 存储系统用户基本信息';
COMMENT ON COLUMN users.id IS '用户唯一标识';
COMMENT ON COLUMN users.username IS '用户名';
COMMENT ON COLUMN users.email IS '邮箱地址';
COMMENT ON COLUMN users.phone IS '手机号码';
COMMENT ON COLUMN users.password_hash IS '密码哈希值';
COMMENT ON COLUMN users.avatar_url IS '头像URL';
COMMENT ON COLUMN users.role IS '用户角色: user/admin/superadmin';
COMMENT ON COLUMN users.is_active IS '账户是否激活';
COMMENT ON COLUMN users.created_at IS '创建时间';
COMMENT ON COLUMN users.updated_at IS '更新时间';

-- ============================================
-- 2. 故事表 (stories)
-- ============================================
CREATE TABLE IF NOT EXISTS stories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50),
    target_age VARCHAR(20),
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    word_count INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_stories_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_stories_status CHECK (status IN ('draft', 'published', 'archived'))
);

COMMENT ON TABLE stories IS '故事表 - 存储用户创建的故事文本';
COMMENT ON COLUMN stories.id IS '故事唯一标识';
COMMENT ON COLUMN stories.user_id IS '创建者用户ID';
COMMENT ON COLUMN stories.title IS '故事标题';
COMMENT ON COLUMN stories.content IS '故事正文内容';
COMMENT ON COLUMN stories.category IS '故事分类';
COMMENT ON COLUMN stories.target_age IS '目标受众年龄';
COMMENT ON COLUMN stories.status IS '状态: draft/published/archived';
COMMENT ON COLUMN stories.word_count IS '故事字数';
COMMENT ON COLUMN stories.created_at IS '创建时间';
COMMENT ON COLUMN stories.updated_at IS '更新时间';

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
    settings JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_projects_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_projects_story FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE SET NULL,
    CONSTRAINT chk_projects_type CHECK (project_type IN ('audio', 'video')),
    CONSTRAINT chk_projects_status CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

COMMENT ON TABLE projects IS '项目表 - 存储生成的音频/视频项目';
COMMENT ON COLUMN projects.id IS '项目唯一标识';
COMMENT ON COLUMN projects.user_id IS '创建者用户ID';
COMMENT ON COLUMN projects.story_id IS '关联的故事ID';
COMMENT ON COLUMN projects.title IS '项目标题';
COMMENT ON COLUMN projects.description IS '项目详细描述内容';
COMMENT ON COLUMN projects.project_type IS '项目类型: audio/video';
COMMENT ON COLUMN projects.style IS '项目样式信息';
COMMENT ON COLUMN projects.file_url IS '项目文件URL';
COMMENT ON COLUMN projects.thumbnail_url IS '缩略图URL';
COMMENT ON COLUMN projects.duration IS '项目时长(秒)';
COMMENT ON COLUMN projects.status IS '状态: pending/processing/completed/failed';
COMMENT ON COLUMN projects.settings IS '生成参数配置(JSON格式)';
COMMENT ON COLUMN projects.created_at IS '创建时间';
COMMENT ON COLUMN projects.updated_at IS '更新时间';

-- ============================================
-- 4. 任务表 (tasks)
-- ============================================
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    input_params JSONB,
    result JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_tasks_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_tasks_status CHECK (status IN ('pending', 'in_progress', 'success', 'failed', 'cancelled')),
    CONSTRAINT chk_tasks_progress CHECK (progress >= 0 AND progress <= 100),
    CONSTRAINT chk_tasks_retry CHECK (retry_count >= 0)
);

COMMENT ON TABLE tasks IS '任务表 - 存储异步任务信息';
COMMENT ON COLUMN tasks.id IS '任务唯一标识';
COMMENT ON COLUMN tasks.user_id IS '创建者用户ID';
COMMENT ON COLUMN tasks.task_type IS '任务类型';
COMMENT ON COLUMN tasks.status IS '状态: pending/in_progress/success/failed/cancelled';
COMMENT ON COLUMN tasks.progress IS '任务进度百分比(0-100)';
COMMENT ON COLUMN tasks.input_params IS '输入参数(JSON格式)';
COMMENT ON COLUMN tasks.result IS '执行结果(JSON格式)';
COMMENT ON COLUMN tasks.error_message IS '错误信息';
COMMENT ON COLUMN tasks.retry_count IS '重试次数';
COMMENT ON COLUMN tasks.started_at IS '开始时间';
COMMENT ON COLUMN tasks.completed_at IS '完成时间';
COMMENT ON COLUMN tasks.created_at IS '创建时间';

-- ============================================
-- 5. 声音模型表 (voice_models)
-- ============================================
CREATE TABLE IF NOT EXISTS voice_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    model_url VARCHAR(500),
    sample_url VARCHAR(500),
    sample_duration INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'training',
    similarity FLOAT DEFAULT 0.8,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT fk_voice_models_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_voice_models_status CHECK (status IN ('training', 'ready', 'failed')),
    CONSTRAINT chk_voice_models_similarity CHECK (similarity >= 0 AND similarity <= 1)
);

COMMENT ON TABLE voice_models IS '声音模型表 - 存储用户个性化声音模型';
COMMENT ON COLUMN voice_models.id IS '模型唯一标识';
COMMENT ON COLUMN voice_models.user_id IS '所有者用户ID';
COMMENT ON COLUMN voice_models.name IS '模型名称';
COMMENT ON COLUMN voice_models.model_url IS '模型文件URL';
COMMENT ON COLUMN voice_models.sample_url IS '样本音频URL';
COMMENT ON COLUMN voice_models.sample_duration IS '样本音频时长(秒)';
COMMENT ON COLUMN voice_models.status IS '状态: training/ready/failed';
COMMENT ON COLUMN voice_models.similarity IS '声音相似度(0-1)';
COMMENT ON COLUMN voice_models.created_at IS '创建时间';
COMMENT ON COLUMN voice_models.updated_at IS '更新时间';

-- ============================================
-- 索引创建
-- ============================================

-- ============================================
-- 1. 用户表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

-- ============================================
-- 2. 故事表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_stories_user_id ON stories(user_id);
CREATE INDEX IF NOT EXISTS idx_stories_status ON stories(status);
CREATE INDEX IF NOT EXISTS idx_stories_category ON stories(category);
CREATE INDEX IF NOT EXISTS idx_stories_created_at ON stories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_stories_user_status ON stories(user_id, status);

-- ============================================
-- 3. 项目表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_story_id ON projects(story_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_type ON projects(project_type);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_projects_user_status ON projects(user_id, status);

-- ============================================
-- 4. 任务表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(task_type);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_status_created ON tasks(status, created_at DESC);

-- ============================================
-- 5. 声音模型表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_voice_models_user_id ON voice_models(user_id);
CREATE INDEX IF NOT EXISTS idx_voice_models_status ON voice_models(status);
CREATE INDEX IF NOT EXISTS idx_voice_models_created_at ON voice_models(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_voice_models_user_status ON voice_models(user_id, status);

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

-- users 表触发器
CREATE TRIGGER trigger_users_update_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

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

-- ============================================
-- 初始化完成
-- ============================================
