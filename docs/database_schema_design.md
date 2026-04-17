# TaleVoice 数据表结构设计文档

**文档版本**: v1.0  
**创建日期**: 2026-04-15  
**最后更新**: 2026-04-15  
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
  └────< voice_models (N)
  │
  └────< audio_files (N)
          │
          └──────> projects (N)
                    (audio_files.project_id)
```

| 关系 | 说明 | 级联策略 |
|-----|------|---------|
| users → stories | 一对多 | ON DELETE CASCADE |
| users → projects | 一对多 | ON DELETE CASCADE |
| users → voice_models | 一对多 | ON DELETE CASCADE |
| users → audio_files | 一对多 | ON DELETE CASCADE |
| stories → projects | 一对多（双向） | ON DELETE SET NULL |
| projects → audio_files | 一对多 | ON DELETE SET NULL |

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
