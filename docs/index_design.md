# TaleVoice 索引设计说明文档

**文档版本**: v1.0  
**创建日期**: 2026-04-15  
**最后更新**: 2026-04-15  
**数据库**: PostgreSQL 15+

---

## 1. 文档概述

### 1.1 文档目的
本文档详细说明 TaleVoice 项目数据库索引的设计策略，包括各索引的用途、预期性能优化效果及使用场景，为数据库性能优化提供参考依据。

### 1.2 索引设计原则
| 原则 | 说明 |
|-----|------|
| 必要性原则 | 只为频繁查询的字段创建索引 |
| 避免过度索引 | 索引会增加写入开销，避免创建冗余索引 |
| 复合索引策略 | 优先考虑复合索引，提高查询效率 |
| 索引命名规范 | 统一索引命名，便于管理和维护 |
| 定期维护 | 定期分析索引使用情况，删除无用索引 |

### 1.3 索引命名规范
- 格式: `idx_{表名}_{字段名1}_{字段名2}_...`
- 单字段索引: `idx_{表名}_{字段名}`
- 复合索引: `idx_{表名}_{字段1}_{字段2}`
- 示例: `idx_stories_user_id`, `idx_projects_user_status`

---

## 2. 用户表索引 (users)

### 2.1 主键索引
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| pk_users_id | id | PRIMARY KEY | 用户表主键索引 |

**用途**: 唯一标识用户记录，支持高效的单记录查询。

**性能优化**: PostgreSQL 自动为主键创建 B-Tree 索引，查询效率 O(log n)。

---

### 2.2 唯一索引
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| uk_users_username | username | UNIQUE | 用户名唯一索引 |
| uk_users_email | email | UNIQUE | 邮箱唯一索引 |
| uk_users_phone | phone | UNIQUE | 手机号唯一索引 |

**用途**: 
- 确保用户名、邮箱、手机号的唯一性
- 支持通过用户名、邮箱、手机号快速查询用户

**性能优化**: 
- 登录/注册时通过邮箱/用户名/手机号查找用户
- 查询效率: 从全表扫描 O(n) 优化为索引查询 O(log n)

**典型查询场景**:
```sql
-- 用户登录查询
SELECT * FROM users WHERE email = 'user@example.com';

-- 用户注册时检查用户名是否存在
SELECT COUNT(*) FROM users WHERE username = 'testuser';
```

---

### 2.3 普通索引

#### idx_users_role
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_users_role | role | BTREE | 用户角色索引 |

**用途**: 按用户角色筛选用户列表。

**性能优化**: 
- 管理后台查询管理员列表
- 查询效率: 从全表扫描优化为索引范围扫描

**典型查询场景**:
```sql
-- 查询所有管理员
SELECT * FROM users WHERE role = 'admin';
```

---

#### idx_users_is_active
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_users_is_active | is_active | BTREE | 账户激活状态索引 |

**用途**: 筛选活跃用户或禁用用户。

**性能优化**: 
- 批量查询活跃用户
- 查询效率: 快速过滤非活跃用户

**典型查询场景**:
```sql
-- 查询所有活跃用户
SELECT * FROM users WHERE is_active = TRUE;
```

---

#### idx_users_created_at
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_users_created_at | created_at | BTREE (DESC) | 用户创建时间索引（降序） |

**用途**: 按创建时间排序和分页查询用户。

**性能优化**: 
- 用户列表按注册时间倒序排列
- 支持时间范围查询
- 查询效率: 避免全表排序

**典型查询场景**:
```sql
-- 查询最近注册的用户（分页）
SELECT * FROM users 
ORDER BY created_at DESC 
LIMIT 20 OFFSET 0;

-- 查询指定时间段注册的用户
SELECT * FROM users 
WHERE created_at BETWEEN '2026-01-01' AND '2026-04-15';
```

---

## 3. 故事表索引 (stories)

### 3.1 主键索引
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| pk_stories_id | id | PRIMARY KEY | 故事表主键索引 |

**用途**: 唯一标识故事记录。

---

### 3.2 外键索引

#### idx_stories_user_id
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_stories_user_id | user_id | BTREE | 用户ID外键索引 |

**用途**: 查询指定用户的所有故事。

**性能优化**: 
- 这是最频繁的查询之一
- 查询效率: 从全表扫描 O(n) 优化为索引查询 O(log n)

**典型查询场景**:
```sql
-- 查询用户的所有故事
SELECT * FROM stories WHERE user_id = 'user-uuid';
```

---

### 3.3 状态索引

#### idx_stories_status
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_stories_status | status | BTREE | 故事状态索引 |

**用途**: 按状态筛选故事（草稿/已发布/已归档）。

**性能优化**: 
- 查询用户的已发布故事
- 查询效率: 快速过滤特定状态的故事

**典型查询场景**:
```sql
-- 查询用户已发布的故事
SELECT * FROM stories 
WHERE user_id = 'user-uuid' AND status = 'published';
```

---

### 3.4 分类索引

#### idx_stories_category
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_stories_category | category | BTREE | 故事分类索引 |

**用途**: 按分类筛选故事。

**性能优化**: 
- 分类浏览功能
- 查询效率: 支持按分类快速筛选

**典型查询场景**:
```sql
-- 查询童话类故事
SELECT * FROM stories WHERE category = '童话';
```

---

### 3.5 时间索引

#### idx_stories_created_at
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_stories_created_at | created_at | BTREE (DESC) | 故事创建时间索引（降序） |

**用途**: 按创建时间排序和分页查询故事。

**性能优化**: 
- 故事列表按时间倒序排列
- 支持时间范围查询
- 查询效率: 避免全表排序

**典型查询场景**:
```sql
-- 用户故事列表（分页）
SELECT * FROM stories 
WHERE user_id = 'user-uuid' 
ORDER BY created_at DESC 
LIMIT 10 OFFSET 0;
```

---

### 3.6 复合索引

#### idx_stories_user_status
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_stories_user_status | user_id, status | BTREE | 用户ID + 状态复合索引 |

**用途**: 查询指定用户特定状态的故事。

**设计考量**: 
- 最左前缀原则：user_id 在前面，可单独用于查询用户的故事
- status 在后面，可与 user_id 组合查询

**性能优化**: 
- 这是最高频的查询之一
- 避免了使用两个单独索引后的回表操作
- 查询效率: 单次索引扫描即可完成

**典型查询场景**:
```sql
-- 查询用户的草稿
SELECT * FROM stories 
WHERE user_id = 'user-uuid' AND status = 'draft';

-- 查询用户的已发布故事
SELECT * FROM stories 
WHERE user_id = 'user-uuid' AND status = 'published';
```

---

## 4. 项目表索引 (projects)

### 4.1 主键索引
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| pk_projects_id | id | PRIMARY KEY | 项目表主键索引 |

**用途**: 唯一标识项目记录。

---

### 4.2 外键索引

#### idx_projects_user_id
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_projects_user_id | user_id | BTREE | 用户ID外键索引 |

**用途**: 查询指定用户的所有项目。

**性能优化**: 
- 用户项目列表查询
- 查询效率: 从全表扫描优化为索引查询

**典型查询场景**:
```sql
-- 查询用户的所有项目
SELECT * FROM projects WHERE user_id = 'user-uuid';
```

---

#### idx_projects_story_id
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_projects_story_id | story_id | BTREE | 故事ID外键索引 |

**用途**: 查询指定故事生成的所有项目。

**性能优化**: 
- 查看某个故事的历史生成记录
- 查询效率: 支持按故事快速查找项目

**典型查询场景**:
```sql
-- 查询某个故事生成的所有项目
SELECT * FROM projects WHERE story_id = 'story-uuid';
```

---

### 4.3 状态索引

#### idx_projects_status
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_projects_status | status | BTREE | 项目状态索引 |

**用途**: 按状态筛选项目。

**性能优化**: 
- 查询正在处理中的项目
- 查询已完成的项目
- 查询效率: 快速过滤特定状态

**典型查询场景**:
```sql
-- 查询用户正在处理的项目
SELECT * FROM projects 
WHERE user_id = 'user-uuid' AND status = 'processing';
```

---

### 4.4 类型索引

#### idx_projects_type
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_projects_type | project_type | BTREE | 项目类型索引 |

**用途**: 按类型筛选项目（音频/视频）。

**性能优化**: 
- 分别展示音频和视频项目
- 查询效率: 支持按类型快速筛选

**典型查询场景**:
```sql
-- 查询用户的音频项目
SELECT * FROM projects 
WHERE user_id = 'user-uuid' AND project_type = 'audio';
```

---

### 4.5 时间索引

#### idx_projects_created_at
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_projects_created_at | created_at | BTREE (DESC) | 项目创建时间索引（降序） |

**用途**: 按创建时间排序和分页查询项目。

**性能优化**: 
- 项目列表按时间倒序排列
- 查询效率: 避免全表排序

**典型查询场景**:
```sql
-- 用户项目列表（分页）
SELECT * FROM projects 
WHERE user_id = 'user-uuid' 
ORDER BY created_at DESC 
LIMIT 10 OFFSET 0;
```

---

### 4.6 复合索引

#### idx_projects_user_status
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_projects_user_status | user_id, status | BTREE | 用户ID + 状态复合索引 |

**用途**: 查询指定用户特定状态的项目。

**设计考量**: 
- 最左前缀原则
- 支持单独查询用户项目，也支持组合查询

**性能优化**: 
- 查询用户已完成的项目
- 查询用户处理中的项目
- 查询效率: 单次索引扫描

**典型查询场景**:
```sql
-- 查询用户已完成的项目
SELECT * FROM projects 
WHERE user_id = 'user-uuid' AND status = 'completed';
```

---

## 5. 任务表索引 (tasks)

### 5.1 主键索引
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| pk_tasks_id | id | PRIMARY KEY | 任务表主键索引 |

**用途**: 唯一标识任务记录。

---

### 5.2 外键索引

#### idx_tasks_user_id
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_tasks_user_id | user_id | BTREE | 用户ID外键索引 |

**用途**: 查询指定用户的所有任务。

**性能优化**: 
- 用户任务列表查询
- 查询效率: 从全表扫描优化为索引查询

**典型查询场景**:
```sql
-- 查询用户的所有任务
SELECT * FROM tasks WHERE user_id = 'user-uuid';
```

---

### 5.3 状态索引

#### idx_tasks_status
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_tasks_status | status | BTREE | 任务状态索引 |

**用途**: 按状态筛选任务。

**性能优化**: 
- 任务调度器查询待处理任务
- 查询进行中的任务
- 查询效率: 快速过滤特定状态

**典型查询场景**:
```sql
-- 查询所有待处理的任务
SELECT * FROM tasks WHERE status = 'pending' ORDER BY created_at ASC;

-- 查询进行中的任务
SELECT * FROM tasks WHERE status = 'in_progress';
```

---

### 5.4 类型索引

#### idx_tasks_type
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_tasks_type | task_type | BTREE | 任务类型索引 |

**用途**: 按类型筛选任务。

**性能优化**: 
- 统计各类任务数量
- 查询效率: 支持按类型快速筛选

**典型查询场景**:
```sql
-- 查询所有语音合成任务
SELECT * FROM tasks WHERE task_type = 'synthesize_audio';
```

---

### 5.5 时间索引

#### idx_tasks_created_at
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_tasks_created_at | created_at | BTREE (DESC) | 任务创建时间索引（降序） |

**用途**: 按创建时间排序和分页查询任务。

**性能优化**: 
- 任务列表按时间倒序排列
- 查询效率: 避免全表排序

**典型查询场景**:
```sql
-- 用户任务列表（分页）
SELECT * FROM tasks 
WHERE user_id = 'user-uuid' 
ORDER BY created_at DESC 
LIMIT 10 OFFSET 0;
```

---

### 5.6 复合索引

#### idx_tasks_user_status
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_tasks_user_status | user_id, status | BTREE | 用户ID + 状态复合索引 |

**用途**: 查询指定用户特定状态的任务。

**设计考量**: 
- 最左前缀原则
- 支持单独查询用户任务，也支持组合查询

**性能优化**: 
- 查询用户进行中的任务
- 查询用户已完成的任务
- 查询效率: 单次索引扫描

**典型查询场景**:
```sql
-- 查询用户进行中的任务
SELECT * FROM tasks 
WHERE user_id = 'user-uuid' AND status = 'in_progress';
```

---

#### idx_tasks_status_created
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_tasks_status_created | status, created_at | BTREE | 状态 + 创建时间复合索引 |

**用途**: 任务调度器按优先级获取待处理任务。

**设计考量**: 
- 任务调度器需要按状态筛选，并按创建时间排序（先到先处理）
- status 在前面，created_at 在后面

**性能优化**: 
- 任务调度查询
- 查询效率: 避免排序操作

**典型查询场景**:
```sql
-- 任务调度器获取待处理任务
SELECT * FROM tasks 
WHERE status = 'pending' 
ORDER BY created_at ASC 
LIMIT 10;
```

---

## 6. 声音模型表索引 (voice_models)

### 6.1 主键索引
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| pk_voice_models_id | id | PRIMARY KEY | 声音模型表主键索引 |

**用途**: 唯一标识声音模型记录。

---

### 6.2 外键索引

#### idx_voice_models_user_id
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_voice_models_user_id | user_id | BTREE | 用户ID外键索引 |

**用途**: 查询指定用户的所有声音模型。

**性能优化**: 
- 用户声音模型列表查询
- 查询效率: 从全表扫描优化为索引查询

**典型查询场景**:
```sql
-- 查询用户的所有声音模型
SELECT * FROM voice_models WHERE user_id = 'user-uuid';
```

---

### 6.3 状态索引

#### idx_voice_models_status
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_voice_models_status | status | BTREE | 声音模型状态索引 |

**用途**: 按状态筛选声音模型。

**性能优化**: 
- 查询训练中的模型
- 查询可用的模型
- 查询效率: 快速过滤特定状态

**典型查询场景**:
```sql
-- 查询用户可用的声音模型
SELECT * FROM voice_models 
WHERE user_id = 'user-uuid' AND status = 'ready';
```

---

### 6.4 时间索引

#### idx_voice_models_created_at
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_voice_models_created_at | created_at | BTREE (DESC) | 声音模型创建时间索引（降序） |

**用途**: 按创建时间排序和分页查询声音模型。

**性能优化**: 
- 模型列表按时间倒序排列
- 查询效率: 避免全表排序

**典型查询场景**:
```sql
-- 用户声音模型列表
SELECT * FROM voice_models 
WHERE user_id = 'user-uuid' 
ORDER BY created_at DESC;
```

---

### 6.5 复合索引

#### idx_voice_models_user_status
| 索引名 | 字段 | 类型 | 说明 |
|-------|------|------|------|
| idx_voice_models_user_status | user_id, status | BTREE | 用户ID + 状态复合索引 |

**用途**: 查询指定用户特定状态的声音模型。

**设计考量**: 
- 最左前缀原则
- 支持单独查询用户模型，也支持组合查询

**性能优化**: 
- 查询用户可用的声音模型
- 查询用户训练中的模型
- 查询效率: 单次索引扫描

**典型查询场景**:
```sql
-- 查询用户可用的声音模型
SELECT * FROM voice_models 
WHERE user_id = 'user-uuid' AND status = 'ready';
```

---

## 7. 索引维护策略

### 7.1 定期分析索引使用情况

使用 PostgreSQL 提供的系统视图监控索引使用情况：

```sql
-- 查看索引使用情况
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- 查看未使用的索引
SELECT 
    schemaname || '.' || relname AS table,
    indexrelname AS index
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND schemaname NOT IN ('pg_catalog', 'information_schema');
```

### 7.2 索引重建和优化

```sql
-- 重建索引
REINDEX INDEX idx_stories_user_id;

-- 重建表的所有索引
REINDEX TABLE stories;

-- 分析表统计信息
ANALYZE stories;
```

### 7.3 监控索引膨胀

```sql
-- 查看索引大小
SELECT 
    indexrelname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;
```

---

## 8. 索引使用最佳实践

### 8.1 查询优化建议

1. **利用最左前缀原则**
   - 复合索引中，字段顺序很重要
   - 确保查询条件与索引前缀匹配

2. **避免在索引字段上使用函数**
   ```sql
   -- 不推荐（无法使用索引）
   SELECT * FROM users WHERE LOWER(email) = 'user@example.com';
   
   -- 推荐
   SELECT * FROM users WHERE email = LOWER('user@example.com');
   ```

3. **使用覆盖索引减少回表**
   - 索引包含查询所需的所有字段
   - 避免从主表获取数据

### 8.2 写入性能考虑

- 索引会增加写入操作的开销
- 写入频繁的表，避免创建过多索引
- 考虑批量写入后重建索引

---

## 9. 性能预期

| 查询场景 | 无索引 | 有索引 | 提升 |
|---------|-------|-------|------|
| 按用户ID查询故事 | O(n) | O(log n) | 显著 |
| 按状态筛选故事 | O(n) | O(log n) | 显著 |
| 用户+状态复合查询 | O(n) | O(log n) | 显著 |
| 按时间排序分页 | O(n log n) | O(log n) | 显著 |
| 任务调度查询 | O(n log n) | O(log n) | 显著 |

---

*文档结束*
