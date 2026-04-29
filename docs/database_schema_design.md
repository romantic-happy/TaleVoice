# TaleVoice 数据表结构设计文档

**文档版本**: v3.0  
**创建日期**: 2026-04-15  
**最后更新**: 2026-04-24  
**数据库**: PostgreSQL 15+

---

## 1. 文档概述

### 1.1 文档目的
本文档详细说明 TaleVoice 项目核心数据表的设计，包括字段定义、数据类型、约束条件及设计考量，为数据库开发和维护提供参考依据。

### 1.2 设计原则
| 原则 | 说明 |
|-----|------|
| 第三范式 | 减少数据冗余，避免更新异常 |
| 规范化命名 | 使用有意义的字段名称，统一命名规范 |
| 合适的类型 | 选择合适的数据类型，确保存储效率和数据准确性 |
| 完整约束 | 定义主键、外键、非空、唯一等约束保证数据完整性 |
| 注释完善 | 为重要字段添加适当的注释说明 |

### 1.3 命名规范
- **表名**: 使用复数形式，小写，下划线分隔（如: users, stories）
- **字段名**: 小写，下划线分隔（如: user_id, created_at）
- **约束名**: 使用前缀（如: pk_, uk_, fk_, chk_）
- **索引名**: 使用前缀 idx_，包含表名和字段名（如: idx_users_email）

---

## 2. 核心数据表设计

### 2.1 用户表 (users)

#### 表说明
存储系统用户的基本信息，包括认证信息和个人资料。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|-------|---------|------|--------|------|
| id | UUID | PK, NOT NULL | gen_random_uuid() | 用户唯一标识 |
| username | VARCHAR(50) | UK, NOT NULL | - | 用户名 |
| email | VARCHAR(100) | UK, NOT NULL | - | 邮箱地址 |
| password_hash | VARCHAR(255) | NOT NULL | - | 密码哈希值（bcrypt加密） |
| avatar_url | VARCHAR(500) | - | NULL | 头像URL |
| created_at | TIMESTAMP | NOT NULL | NOW() | 创建时间 |

#### 约束定义

| 约束名 | 类型 | 说明 |
|-------|------|------|
| pk_users_id | PRIMARY KEY | 主键约束 |
| uk_users_username | UNIQUE | 用户名唯一约束 |
| uk_users_email | UNIQUE | 邮箱唯一约束 |

#### 设计考量
- 使用 UUID 作为主键，便于分布式系统和数据迁移
- 密码使用 bcrypt 哈希存储，不存储明文
- 支持邮箱登录方式

---

### 2.2 故事表 (stories)

#### 表说明
存储用户创建的故事文本内容，包括标题、正文、分类等信息。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|-------|---------|------|--------|------|
| id | UUID | PK, NOT NULL | gen_random_uuid() | 故事唯一标识 |
| user_id | UUID | FK, NOT NULL | - | 创建者用户ID（外键 → users.id） |
| title | VARCHAR(200) | NOT NULL | - | 故事标题 |
| content | TEXT | NOT NULL | - | 故事正文内容 |
| created_at | TIMESTAMP | NOT NULL | NOW() | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | NOW() | 更新时间（自动更新） |
| project_id | UUID | FK | NULL | 关联的项目ID（外键 → projects.id） |
#### 约束定义

| 约束名 | 类型 | 说明 |
|-------|------|------|
| pk_stories_id | PRIMARY KEY | 主键约束 |
| fk_stories_user | FOREIGN KEY | 外键约束（级联删除） |
| fk_stories_project | FOREIGN KEY | 外键约束（置空） |

#### 设计考量
- user_id 使用级联删除，删除用户时自动删除其所有故事
- content 使用 TEXT 类型，支持长文本存储

---

### 2.3 项目表 (projects)

#### 表说明
存储生成的音频或视频项目，包括文件信息、状态、生成参数等。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|-------|---------|------|--------|------|
| id | UUID | PK, NOT NULL | gen_random_uuid() | 项目唯一标识 |
| user_id | UUID | FK, NOT NULL | - | 创建者用户ID（外键 → users.id） |
| story_id | UUID | FK | NULL | 关联的故事ID（外键 → stories.id） |
| title | VARCHAR(200) | NOT NULL | - | 项目标题 |
| description | TEXT | - | NULL | 项目详细描述内容 |
| project_type | VARCHAR(20) | NOT NULL, CHECK | - | 项目类型: audio/video |
| style | VARCHAR(100) | - | 'default' | 项目风格 |
| file_url | VARCHAR(500) | - | NULL | 项目文件URL |
| thumbnail_url | VARCHAR(500) | - | NULL | 缩略图URL |
| duration | INTEGER | - | NULL | 项目时长（秒） |
| status | VARCHAR(20) | NOT NULL, CHECK | 'processing' | 状态: pending/processing/completed/failed |
| created_at | TIMESTAMP | NOT NULL | NOW() | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | NOW() | 更新时间（自动更新） |

#### 约束定义

| 约束名 | 类型 | 说明 |
|-------|------|------|
| pk_projects_id | PRIMARY KEY | 主键约束 |
| fk_projects_user | FOREIGN KEY | 外键约束（级联删除） |
| fk_projects_story | FOREIGN KEY | 外键约束（置空） |
| chk_projects_type | CHECK | 类型值必须为 audio/video |
| chk_projects_status | CHECK | 状态值必须为 pending/processing/completed/failed |

#### 设计考量
- story_id 使用 SET NULL，删除故事时不删除关联项目
- project_type 区分音频和视频项目
- description 使用 TEXT 类型支持长文本描述
- style 字段存储项目样式配置，默认值为 'default'
- settings 使用 JSONB 类型存储灵活的生成参数
- status 字段跟踪项目生成进度
- duration 记录项目时长便于展示




---

### 2.4 声音模型表 (voice_models)

#### 表说明
存储用户的个性化声音模型信息，包括模型文件、训练状态等。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|-------|---------|------|--------|------|
| id | UUID | PK, NOT NULL | gen_random_uuid() | 模型唯一标识 |
| user_id | UUID | FK, NOT NULL | - | 所有者用户ID（外键 → users.id） |
| name | VARCHAR(100) | NOT NULL | - | 模型名称 |
| model_url | VARCHAR(500) | - | NULL | 模型文件URL |
| sample_url | VARCHAR(500) | - | NULL | 样本音频URL |
| sample_duration | INTEGER | - | NULL | 样本音频时长（秒） |
| status | VARCHAR(20) | NOT NULL, CHECK | 'training' | 状态: training/ready/failed |
| similarity | FLOAT | NOT NULL, CHECK | 0.8 | 声音相似度（0-1） |
| created_at | TIMESTAMP | NOT NULL | NOW() | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | NOW() | 更新时间（自动更新） |

#### 约束定义

| 约束名 | 类型 | 说明 |
|-------|------|------|
| pk_voice_models_id | PRIMARY KEY | 主键约束 |
| fk_voice_models_user | FOREIGN KEY | 外键约束（级联删除） |
| chk_voice_models_status | CHECK | 状态值必须为 training/ready/failed |
| chk_voice_models_similarity | CHECK | 相似度值必须在 0-1 之间 |

#### 设计考量
- user_id 使用级联删除，删除用户时自动删除其所有声音模型
- sample_duration 验证音频样本是否满足最低时长要求
- similarity 记录声音模型的相似度指标
- status 跟踪模型训练进度

---
### 2.5 音频表 (audio_files)

#### 表说明
存储用户的个性化音频信息，包括音频文件、训练状态等。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|-------|---------|------|--------|------|
| id | UUID | PK, NOT NULL | gen_random_uuid() | 音频唯一标识 |
| user_id | UUID | FK, NOT NULL | - | 所有者用户ID（外键 → users.id） |
| name | VARCHAR(100) | NOT NULL | - | 音频名称 |
| file_url | VARCHAR(500) | - | NULL | 音频文件URL |
| title | VARCHAR(100) | NOT NULL | - | 音频标题 |
| created_at | TIMESTAMP | NOT NULL | NOW() | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | NOW() | 更新时间（自动更新） |
| project_id | UUID | FK | NULL | 关联的项目ID（外键 → projects.id） |

---

### 2.6 视频表 (videos)

#### 表说明
存储由图片通过大模型生成的视频信息，包括源图片、生成的视频文件、视频属性等。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|-------|---------|------|--------|------|
| id | UUID | PK, NOT NULL | gen_random_uuid() | 视频唯一标识 |
| project_id | UUID | FK, NOT NULL | - | 关联的项目ID（外键 → projects.id） |
| user_id | UUID | FK, NOT NULL | - | 所有者用户ID（外键 → users.id） |
| title | VARCHAR(200) | NOT NULL | - | 视频标题 |
| description | TEXT | - | NULL | 视频描述 |
| source_image_url | VARCHAR(500) | - | NULL | 源图片URL（生成视频的原始图片） |
| file_url | VARCHAR(500) | - | NULL | 视频文件URL |
| thumbnail_url | VARCHAR(500) | - | NULL | 缩略图URL |
| duration | INTEGER | - | NULL | 视频时长（秒） |
| resolution | VARCHAR(20) | - | NULL | 视频分辨率（如 1920x1080） |
| fps | INTEGER | - | NULL | 帧率（每秒帧数） |
| file_size | BIGINT | - | NULL | 文件大小（字节） |
| format | VARCHAR(20) | - | 'mp4' | 视频格式 |
| created_at | TIMESTAMP | NOT NULL | NOW() | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | NOW() | 更新时间（自动更新） |

#### 约束定义

| 约束名 | 类型 | 说明 |
|-------|------|------|
| pk_videos_id | PRIMARY KEY | 主键约束 |
| fk_videos_project | FOREIGN KEY | 外键约束（级联删除） |
| fk_videos_user | FOREIGN KEY | 外键约束（级联删除） |

#### 设计考量
- project_id 使用级联删除，删除项目时自动删除关联视频
- user_id 作为冗余字段，便于快速查询用户的所有视频
- source_image_url 记录生成视频的原始图片地址
- resolution 和 fps 记录视频的技术参数
- file_size 用于存储空间管理和统计
- bgm_id 关联背景音乐，支持视频配乐功能
- bgm_volume、bgm_fade_in、bgm_fade_out、bgm_loop 提供精细的背景音乐控制

---

### 2.7 背景音乐表 (bgm)

#### 表说明
存储系统预置和用户上传的背景音乐资源信息，支持按情感、风格分类检索。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|-------|---------|------|--------|------|
| id | UUID | PK, NOT NULL | gen_random_uuid() | 背景音乐唯一标识 |
| name | VARCHAR(256) | NOT NULL | - | 音乐名称 |
| user_id | UUID | FK | NULL | 上传用户ID（系统预置为NULL） |
| source | VARCHAR(32) | NOT NULL, CHECK | 'system' | 来源类型: system/user/third_party |
| style | VARCHAR(128) | - | NULL | 音乐风格（如：轻快、舒缓、激昂） |
| emotion | VARCHAR(64) | - | NULL | 情感标签（如：温馨、欢快、悲伤） |
| file_url | VARCHAR(512) | - | NULL | 音乐文件URL |
| sample_url | VARCHAR(512) | - | NULL | 试听片段URL |
| duration | INTEGER | - | NULL | 音乐时长（秒） |
| bpm | INTEGER | - | NULL | 节奏BPM（每分钟节拍数） |
| format | VARCHAR(32) | - | 'mp3' | 音频格式（mp3/wav/aac等） |
| sample_rate | INTEGER | - | NULL | 采样率（Hz） |
| channels | INTEGER | - | NULL | 声道数 |
| bit_rate | INTEGER | - | NULL | 比特率（kbps） |
| file_size | BIGINT | - | NULL | 文件大小（字节） |
| play_count | INTEGER | NOT NULL | 0 | 播放次数 |
| created_at | TIMESTAMP | NOT NULL | NOW() | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | NOW() | 更新时间（自动更新） |

#### 约束定义

| 约束名 | 类型 | 说明 |
|-------|------|------|
| pk_bgm_id | PRIMARY KEY | 主键约束 |
| fk_bgm_user | FOREIGN KEY | 外键约束（置空） |
| chk_bgm_source | CHECK | 来源值必须为 system/user/third_party |

#### 设计考量
- user_id 使用 SET NULL，系统预置音乐不关联用户
- source 区分音乐来源，便于管理和计费
- emotion 和 style 支持智能推荐匹配
- play_count 用于热门排序

---

### 2.8 字幕表 (subtitles)

#### 表说明
存储视频字幕生成任务和结果信息，支持多种字幕格式。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|-------|---------|------|--------|------|
| id | UUID | PK, NOT NULL | gen_random_uuid() | 字幕唯一标识 |
| video_id | UUID | FK, NOT NULL | - | 关联视频ID（外键 → videos.id） |
| user_id | UUID | FK, NOT NULL | - | 创建用户ID（外键 → users.id） |
| title | VARCHAR(256) | - | NULL | 字幕标题 |
| language | VARCHAR(16) | - | 'zh-CN' | 语言代码（zh-CN/en-US等） |
| format | VARCHAR(10) | NOT NULL, CHECK | 'srt' | 字幕格式: srt/ass/vtt/json |
| content | TEXT | - | NULL | 字幕内容文本 |
| file_url | VARCHAR(512) | - | NULL | 字幕文件URL |
| task_id | VARCHAR(128) | - | NULL | 阿里云字幕生成任务ID |
| status | VARCHAR(20) | NOT NULL, CHECK | 'pending' | 任务状态: pending/processing/completed/failed |
| confidence | FLOAT | - | NULL | 整体识别置信度（0-1） |
| created_at | TIMESTAMP | NOT NULL | NOW() | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | NOW() | 更新时间（自动更新） |

#### 约束定义

| 约束名 | 类型 | 说明 |
|-------|------|------|
| pk_subtitles_id | PRIMARY KEY | 主键约束 |
| fk_subtitles_video | FOREIGN KEY | 外键约束（级联删除） |
| fk_subtitles_user | FOREIGN KEY | 外键约束（级联删除） |
| chk_subtitles_format | CHECK | 格式值必须为 srt/ass/vtt/json |
| chk_subtitles_status | CHECK | 状态值必须为 pending/processing/completed/failed |

#### 设计考量
- video_id 使用级联删除，删除视频时自动删除关联字幕
- task_id 记录阿里云任务ID，便于状态查询
- confidence 记录整体识别质量

---

### 2.9 字幕片段表 (subtitle_segments)

#### 表说明
存储字幕的具体时间片段和文本内容，实现毫秒级精准对齐。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|-------|---------|------|--------|------|
| id | UUID | PK, NOT NULL | gen_random_uuid() | 片段唯一标识 |
| subtitle_id | UUID | FK, NOT NULL | - | 关联字幕ID（外键 → subtitles.id） |
| segment_index | INTEGER | NOT NULL | - | 片段序号（从1开始） |
| start_time | BIGINT | NOT NULL, CHECK | - | 开始时间（毫秒） |
| end_time | BIGINT | NOT NULL, CHECK | - | 结束时间（毫秒） |
| text | TEXT | NOT NULL | - | 字幕文本内容 |
| confidence | FLOAT | NOT NULL, CHECK | 1.0 | 片段识别置信度（0-1） |
| created_at | TIMESTAMP | NOT NULL | NOW() | 创建时间 |

#### 约束定义

| 约束名 | 类型 | 说明 |
|-------|------|------|
| pk_subtitle_segments_id | PRIMARY KEY | 主键约束 |
| fk_subtitle_segments_subtitle | FOREIGN KEY | 外键约束（级联删除） |
| chk_subtitle_segments_time | CHECK | 时间有效性约束 |
| chk_subtitle_segments_confidence | CHECK | 置信度范围约束 |

#### 设计考量
- start_time 和 end_time 使用 BIGINT 存储毫秒级时间戳
- segment_index 保证片段顺序
- confidence 记录每个片段的识别质量

---

### 2.10 剪辑任务表 (edit_tasks)

#### 表说明
存储视频智能剪辑任务信息和结果，支持多段视频拼接、转场、滤镜等功能。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|-------|---------|------|--------|------|
| id | UUID | PK, NOT NULL | gen_random_uuid() | 剪辑任务唯一标识 |
| project_id | UUID | FK, NOT NULL | - | 关联项目ID（外键 → projects.id） |
| user_id | UUID | FK, NOT NULL | - | 创建用户ID（外键 → users.id） |
| title | VARCHAR(256) | NOT NULL | - | 任务标题 |
| description | TEXT | - | NULL | 任务描述 |
| timeline_config | JSONB | - | NULL | 时间线配置（JSON格式） |
| output_url | VARCHAR(512) | - | NULL | 输出视频URL |
| output_duration | INTEGER | - | NULL | 输出视频时长（秒） |
| resolution | VARCHAR(20) | - | '1920x1080' | 输出分辨率 |
| fps | INTEGER | - | 30 | 输出帧率 |
| task_id | VARCHAR(128) | - | NULL | 阿里云剪辑任务ID |
| status | VARCHAR(20) | NOT NULL, CHECK | 'pending' | 任务状态: pending/processing/completed/failed |
| progress | INTEGER | NOT NULL, CHECK | 0 | 任务进度（0-100） |
| error_message | TEXT | - | NULL | 错误信息 |
| created_at | TIMESTAMP | NOT NULL | NOW() | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | NOW() | 更新时间（自动更新） |

#### 约束定义

| 约束名 | 类型 | 说明 |
|-------|------|------|
| pk_edit_tasks_id | PRIMARY KEY | 主键约束 |
| fk_edit_tasks_project | FOREIGN KEY | 外键约束（级联删除） |
| fk_edit_tasks_user | FOREIGN KEY | 外键约束（级联删除） |
| chk_edit_tasks_status | CHECK | 状态值必须为 pending/processing/completed/failed |
| chk_edit_tasks_progress | CHECK | 进度值必须在 0-100 之间 |

#### 设计考量
- timeline_config 使用 JSONB 存储复杂的时间线配置
- progress 字段支持前端进度展示
- error_message 记录失败原因

---

### 2.11 剪辑片段表 (edit_clips)

#### 表说明
存储剪辑任务中各视频片段的详细配置，包括转场效果、滤镜等。

#### 字段定义

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|-------|---------|------|--------|------|
| id | UUID | PK, NOT NULL | gen_random_uuid() | 片段唯一标识 |
| edit_task_id | UUID | FK, NOT NULL | - | 关联剪辑任务ID（外键 → edit_tasks.id） |
| video_id | UUID | FK | NULL | 关联视频ID（外键 → videos.id） |
| video_url | VARCHAR(512) | NOT NULL | - | 视频文件URL |
| clip_order | INTEGER | NOT NULL | - | 片段顺序（从1开始） |
| start_time | FLOAT | - | 0 | 片段开始时间（秒） |
| end_time | FLOAT | - | 0 | 片段结束时间（秒） |
| duration | FLOAT | - | 0 | 片段时长（秒） |
| transition_in | VARCHAR(32) | NOT NULL, CHECK | 'fade' | 入场转场效果 |
| transition_out | VARCHAR(32) | NOT NULL, CHECK | 'fade' | 出场转场效果 |
| transition_duration | FLOAT | - | 0.5 | 转场时长（秒） |
| filter_type | VARCHAR(32) | NOT NULL, CHECK | 'none' | 滤镜类型 |
| volume | INTEGER | NOT NULL, CHECK | 100 | 音量（0-100） |
| created_at | TIMESTAMP | NOT NULL | NOW() | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | NOW() | 更新时间（自动更新） |

#### 约束定义

| 约束名 | 类型 | 说明 |
|-------|------|------|
| pk_edit_clips_id | PRIMARY KEY | 主键约束 |
| fk_edit_clips_edit_task | FOREIGN KEY | 外键约束（级联删除） |
| fk_edit_clips_video | FOREIGN KEY | 外键约束（置空） |
| chk_edit_clips_volume | CHECK | 音量值必须在 0-100 之间 |
| chk_edit_clips_transition | CHECK | 转场效果值必须在允许范围内 |
| chk_edit_clips_filter | CHECK | 滤镜类型值必须在允许范围内 |

#### 设计考量
- edit_task_id 使用级联删除，删除任务时自动删除关联片段
- video_id 使用 SET NULL，保留片段配置即使视频被删除
- clip_order 保证片段播放顺序
- transition_in/out 支持12种转场效果
- filter_type 支持10种滤镜效果

---
## 3. 表关系图

```
users (1) ──────< stories (N)
  │                  │
  │                  │
  └────< projects (N)│
  │         │        │
  │         │        └──────> projects (N)
  │         │                 (stories.project_id)
  │         │
  │         └──────> stories (N)
  │                   (projects.story_id)
  │
  ├────< voice_models (N)
  │
  ├────< audio_files (N)
  │         │
  │         └──────> projects (N)
  │                   (audio_files.project_id)
  │
  ├────< videos (N)
  │         │
  │         ├──────> projects (N)
  │         │         (videos.project_id)
  │         │
  │         └──────> bgm (N)
  │                   (videos.bgm_id)
  │
  ├────< bgm (N)
  │
  ├────< subtitles (N)
  │         │
  │         └──────> videos (N)
  │                   (subtitles.video_id)
  │
  ├────< subtitle_segments (N)
  │         │
  │         └──────> subtitles (N)
  │                   (subtitle_segments.subtitle_id)
  │
  ├────< edit_tasks (N)
  │         │
  │         └──────> projects (N)
  │                   (edit_tasks.project_id)
  │
  └────< edit_clips (N)
            │
            ├──────> edit_tasks (N)
            │         (edit_clips.edit_task_id)
            │
            └──────> videos (N)
                      (edit_clips.video_id)
```

| 关系 | 说明 | 级联策略 |
|-----|------|---------|
| users → stories | 一对多 | ON DELETE CASCADE |
| users → projects | 一对多 | ON DELETE CASCADE |
| users → voice_models | 一对多 | ON DELETE CASCADE |
| users → audio_files | 一对多 | ON DELETE CASCADE |
| users → videos | 一对多 | ON DELETE CASCADE |
| users → bgm | 一对多 | ON DELETE SET NULL |
| users → subtitles | 一对多 | ON DELETE CASCADE |
| users → edit_tasks | 一对多 | ON DELETE CASCADE |
| stories → projects | 一对多（双向） | ON DELETE SET NULL |
| projects → audio_files | 一对多 | ON DELETE SET NULL |
| projects → videos | 一对多 | ON DELETE CASCADE |
| projects → edit_tasks | 一对多 | ON DELETE CASCADE |
| videos → subtitles | 一对多 | ON DELETE CASCADE |
| videos → edit_clips | 一对多 | ON DELETE SET NULL |
| videos → bgm | 多对一 | ON DELETE SET NULL |
| subtitles → subtitle_segments | 一对多 | ON DELETE CASCADE |
| edit_tasks → edit_clips | 一对多 | ON DELETE CASCADE |

---

## 4. 触发器设计

### 4.1 updated_at 自动更新触发器

为所有包含 updated_at 字段的表创建自动更新触发器，确保数据更新时时间戳自动更新。

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### 4.2 应用触发器的表

| 表名 | 触发器名 |
|-----|---------|
| stories | trigger_stories_update_updated_at |
| projects | trigger_projects_update_updated_at |
| voice_models | trigger_voice_models_update_updated_at |
| audio_files | trigger_audio_files_update_updated_at |
| videos | trigger_videos_update_updated_at |
| bgm | trigger_bgm_update_updated_at |
| subtitles | trigger_subtitles_update_updated_at |
| edit_tasks | trigger_edit_tasks_update_updated_at |
| edit_clips | trigger_edit_clips_update_updated_at |

---

## 5. 扩展性设计

### 5.1 预留字段
各表已预留适当的扩展空间，便于未来业务需求变更。

### 5.2 JSONB 字段优势
- 使用 JSONB 类型存储灵活的配置信息
- 支持 GIN 索引，高效查询 JSON 内部字段
- 便于业务逻辑扩展，无需频繁修改表结构

### 5.3 状态枚举扩展
所有 status 字段使用 VARCHAR 配合 CHECK 约束，便于未来添加新状态。

---

## 6. 性能优化考量

### 6.1 索引策略
- 所有外键字段创建索引
- 状态字段创建索引
- 时间戳字段创建降序索引
- 常用查询条件创建复合索引

（详细索引设计请参考 [索引设计说明文档](index_design.md)）

### 6.2 分区表预留
考虑到未来数据量增长，表设计已考虑分区扩展的可能性。

---

## 7. 数据库部署建议

### 7.1 PostgreSQL 版本
- 推荐使用 PostgreSQL 15 或更高版本
- 利用最新版本的性能优化和新特性

### 7.2 连接池配置
- 使用连接池（如 PgBouncer）管理数据库连接
- 合理配置最大连接数和超时时间

### 7.3 备份策略
- 每日自动全量备份
- 保留最近 30 天的备份
- 定期测试备份恢复

---

*文档结束*
