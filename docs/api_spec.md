# TaleVoice API接口说明文档

## 1. 文档概述

### 1.1 文档目的
本文档详细描述童话之声（TaleVoice）系统的所有API接口，包括接口地址、请求方式、参数说明、返回格式等，为前后端联调提供完整的技术依据。

### 1.2 接口基础信息
| 项目 | 说明 |
|-----|------|
| 协议 | HTTP/HTTPS |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |
| 认证方式 | Bearer Token (JWT) |
| API版本 | v1 |
| 基础路径 | `/api/v1` |

### 1.3 通用请求头
```
Content-Type: application/json
Authorization: Bearer {access_token}
X-Request-ID: {uuid}
```

### 1.4 通用响应格式
```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

### 1.5 错误响应格式
```json
{
  "code": 1001,
  "message": "错误描述",
  "data": null
}
```

### 1.6 错误码定义
| 错误码 | 描述 |
|-------|------|
| 0 | 成功 |
| 1001 | 用户名已存在 |
| 1002 | 邮箱已注册 |
| 1003 | 密码错误 |
| 1004 | 账号不存在 |
| 1005 | Token过期 |
| 1006 | 无权限访问 |
| 2001 | 资源不存在 |
| 3001 | 操作失败 |
| 5001 | 服务器内部错误 |

---

## 2. 认证模块 API

### 2.1 用户注册
**接口地址**: `/api/v1/auth/register`

**请求方式**: `POST`

**请求参数**:
```json
{
  "username": "string, 用户名, 必填, 3-50字符",
  "email": "string, 邮箱, 必填, 有效邮箱格式",
  "password": "string, 密码, 必填, 至少8位"
}
```

**请求示例**:
```json
{
  "username": "zhangsan",
  "email": "zhangsan@example.com",
  "password": "Pass1234"
}
```

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": "uuid",
    "username": "string",
    "email": "string",
    "access_token": "string",
    "token_type": "Bearer",
    "expires_in": 7200
  }
}
```

---

### 2.2 用户登录
**接口地址**: `/api/v1/auth/login`

**请求方式**: `POST`

**请求参数**:
```json
{
  "account": "string, 账号(邮箱/用户名), 必填",
  "password": "string, 密码, 必填"
}
```

**请求示例**:
```json
{
  "account": "zhangsan@example.com",
  "password": "Pass1234"
}
```

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": "uuid",
    "username": "string",
    "email": "string",
    "avatar_url": "string",
    "access_token": "string",
    "token_type": "Bearer",
    "expires_in": 7200
  }
}
```

---

### 2.3 用户登出
**接口地址**: `/api/v1/auth/logout`

**请求方式**: `POST`

**请求头**: 需要认证

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": null
}
```

---

### 2.4 刷新Token
**接口地址**: `/api/v1/auth/refresh`

**请求方式**: `POST`

**请求参数**:
```json
{
  "refresh_token": "string, 刷新令牌, 必填"
}
```

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "string",
    "expires_in": 7200
  }
}
```

---

## 3. 用户模块 API

### 3.1 获取当前用户信息
**接口地址**: `/api/v1/users/me`

**请求方式**: `GET`

**请求头**: 需要认证

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": "uuid",
    "username": "string",
    "email": "string",
    "phone": "string",
    "avatar_url": "string",
    "role": "user",
    "created_at": "datetime",
    "updated_at": "datetime"
  }
}
```

---

### 3.2 更新用户信息
**接口地址**: `/api/v1/users/me`

**请求方式**: `PUT`

**请求头**: 需要认证

**请求参数**:
```json
{
  "username": "string, 用户名, 可选",
  "phone": "string, 手机号, 可选",
  "avatar_url": "string, 头像URL, 可选"
}
```

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": "uuid",
    "username": "string",
    "email": "string",
    "phone": "string",
    "avatar_url": "string",
    "updated_at": "datetime"
  }
}
```

---

### 3.3 修改密码
**接口地址**: `/api/v1/users/password`

**请求方式**: `POST`

**请求头**: 需要认证

**请求参数**:
```json
{
  "old_password": "string, 原密码, 必填",
  "new_password": "string, 新密码, 必填, 至少8位"
}
```

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": null
}
```

---

## 4. 故事模块 API

### 4.1 创建故事
**接口地址**: `/api/v1/stories`

**请求方式**: `POST`

**请求头**: 需要认证

**请求参数**:
```json
{
  "title": "string, 故事标题, 必填, 最多200字符",
  "content": "string, 故事正文, 必填",
  "category": "string, 分类, 可选",
  "target_age": "string, 目标年龄, 可选"
}
```

**请求示例**:
```json
{
  "title": "狼来了",
  "content": "从前有个牧童，每天都在山上放羊...",
  "category": "寓言",
  "target_age": "3-6岁"
}
```

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "uuid",
    "title": "string",
    "content": "string",
    "category": "string",
    "target_age": "string",
    "status": "draft",
    "word_count": 520,
    "created_at": "datetime",
    "updated_at": "datetime"
  }
}
```

---

### 4.2 获取故事列表
**接口地址**: `/api/v1/stories`

**请求方式**: `GET`

**请求头**: 需要认证

**Query参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|-------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量 |
| status | string | 否 | - | 状态筛选 |
| category | string | 否 | - | 分类筛选 |
| keyword | string | 否 | - | 搜索关键词 |
| sort | string | 否 | created_at | 排序字段 |
| order | string | 否 | desc | 排序方向 |

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "uuid",
        "title": "string",
        "category": "string",
        "target_age": "string",
        "status": "draft",
        "word_count": 520,
        "created_at": "datetime",
        "updated_at": "datetime"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  }
}
```

---

### 4.3 获取故事详情
**接口地址**: `/api/v1/stories/{id}`

**请求方式**: `GET`

**请求头**: 需要认证

**路径参数**:
| 参数名 | 类型 | 说明 |
|-------|------|------|
| id | uuid | 故事ID |

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "uuid",
    "user_id": "uuid",
    "title": "string",
    "content": "string",
    "category": "string",
    "target_age": "string",
    "status": "published",
    "word_count": 520,
    "created_at": "datetime",
    "updated_at": "datetime"
  }
}
```

---

### 4.4 更新故事
**接口地址**: `/api/v1/stories/{id}`

**请求方式**: `PUT`

**请求头**: 需要认证

**路径参数**:
| 参数名 | 类型 | 说明 |
|-------|------|------|
| id | uuid | 故事ID |

**请求参数**:
```json
{
  "title": "string, 故事标题, 可选",
  "content": "string, 故事正文, 可选",
  "category": "string, 分类, 可选",
  "target_age": "string, 目标年龄, 可选",
  "status": "string, 状态, 可选"
}
```

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "uuid",
    "title": "string",
    "content": "string",
    "category": "string",
    "target_age": "string",
    "status": "published",
    "word_count": 520,
    "updated_at": "datetime"
  }
}
```

---

### 4.5 删除故事
**接口地址**: `/api/v1/stories/{id}`

**请求方式**: `DELETE`

**请求头**: 需要认证

**路径参数**:
| 参数名 | 类型 | 说明 |
|-------|------|------|
| id | uuid | 故事ID |

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": null
}
```

---

### 4.6 导入故事
**接口地址**: `/api/v1/stories/import`

**请求方式**: `POST`

**请求头**: 需要认证, Content-Type: multipart/form-data

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| file | file | 是 | 文件(支持txt,md) |
| category | string | 否 | 分类 |

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "imported_count": 10,
    "failed_count": 0,
    "failed_items": []
  }
}
```

---

### 4.7 导出故事
**接口地址**: `/api/v1/stories/{id}/export`

**请求方式**: `GET`

**请求头**: 需要认证

**路径参数**:
| 参数名 | 类型 | 说明 |
|-------|------|------|
| id | uuid | 故事ID |

**Query参数**:
| 参数名 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| format | string | txt | 导出格式(txt/md/json) |

**响应**: 文件下载

---

## 5. 语音模块 API

### 5.1 语音合成
**接口地址**: `/api/v1/audio/synthesize`

**请求方式**: `POST`

**请求头**: 需要认证

**请求参数**:
```json
{
  "story_id": "uuid, 故事ID, 必填",
  "voice_type": "string, 声音类型, 必填, 取值: female/male/child/custom",
  "voice_model_id": "uuid, 自定义声音模型ID, voice_type为custom时必填",
  "speed": "float, 语速, 可选, 默认1.0, 范围0.5-2.0",
  "pitch": "float, 音调, 可选, 默认1.0, 范围0.5-2.0",
  "volume": "float, 音量, 可选, 默认1.0, 范围0.0-1.0",
  "bg_music_id": "uuid, 背景音乐ID, 可选",
  "bg_music_volume": "float, 背景音乐音量, 可选, 默认0.3"
}
```

**请求示例**:
```json
{
  "story_id": "550e8400-e29b-41d4-a716-446655440000",
  "voice_type": "female",
  "speed": 1.0,
  "pitch": 1.0,
  "volume": 1.0,
  "bg_music_volume": 0.3
}
```

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "uuid",
    "status": "pending"
  }
}
```

---

### 5.2 获取语音任务状态
**接口地址**: `/api/v1/audio/tasks/{task_id}`

**请求方式**: `GET`

**请求头**: 需要认证

**路径参数**:
| 参数名 | 类型 | 说明 |
|-------|------|------|
| task_id | uuid | 任务ID |

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "uuid",
    "status": "processing",
    "progress": 60,
    "result": null,
    "error_message": null,
    "created_at": "datetime",
    "updated_at": "datetime"
  }
}
```

---

### 5.3 获取语音结果
**接口地址**: `/api/v1/audio/tasks/{task_id}/result`

**请求方式**: `GET`

**请求头**: 需要认证

**路径参数**:
| 参数名 | 类型 | 说明 |
|-------|------|------|
| task_id | uuid | 任务ID |

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "audio_url": "string",
    "duration": 332,
    "format": "mp3"
  }
}
```

---

### 5.4 音频混音
**接口地址**: `/api/v1/audio/mix`

**请求方式**: `POST`

**请求头**: 需要认证

**请求参数**:
```json
{
  "audio_urls": ["string, 音频URL列表, 必填"],
  "mix_type": "string, 混音类型, 可选, 取值: concatenate/overlay",
  "output_format": "string, 输出格式, 可选, 默认mp3"
}
```

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "uuid",
    "status": "pending"
  }
}
```

---

### 5.5 上传音频样本
**接口地址**: `/api/v1/audio/samples`

**请求方式**: `POST`

**请求头**: 需要认证, Content-Type: multipart/form-data

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| file | file | 是 | 音频文件(支持mp3,wav,m4a) |
| name | string | 是 | 样本名称 |

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "sample_id": "uuid",
    "sample_url": "string",
    "duration": 45,
    "name": "string"
  }
}
```

---

### 5.6 获取背景音乐列表
**接口地址**: `/api/v1/audio/background-music`

**请求方式**: `GET`

**请求头**: 需要认证

**Query参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|-------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量 |

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "uuid",
        "name": "string",
        "url": "string",
        "duration": 180,
        "style": "string"
      }
    ],
    "total": 20,
    "page": 1,
    "page_size": 20
  }
}
```

---

## 6. 声音模型模块 API

### 6.1 创建声音模型
**接口地址**: `/api/v1/audio/voice-models`

**请求方式**: `POST`

**请求头**: 需要认证

**请求参数**:
```json
{
  "name": "string, 模型名称, 必填, 最多100字符",
  "sample_url": "string, 样本音频URL, 必填"
}
```

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "model_id": "uuid",
    "name": "string",
    "status": "training",
    "created_at": "datetime"
  }
}
```

---

### 6.2 获取声音模型列表
**接口地址**: `/api/v1/audio/voice-models`

**请求方式**: `GET`

**请求头**: 需要认证

**Query参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|-------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量 |
| status | string | 否 | - | 状态筛选 |

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "uuid",
        "name": "string",
        "status": "ready",
        "similarity": 0.85,
        "sample_url": "string",
        "created_at": "datetime"
      }
    ],
    "total": 5,
    "page": 1,
    "page_size": 20
  }
}
```

---

### 6.3 获取声音模型详情
**接口地址**: `/api/v1/audio/voice-models/{id}`

**请求方式**: `GET`

**请求头**: 需要认证

**路径参数**:
| 参数名 | 类型 | 说明 |
|-------|------|------|
| id | uuid | 模型ID |

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "uuid",
    "user_id": "uuid",
    "name": "string",
    "model_url": "string",
    "sample_url": "string",
    "sample_duration": 45,
    "status": "ready",
    "similarity": 0.85,
    "created_at": "datetime",
    "updated_at": "datetime"
  }
}
```

---

### 6.4 删除声音模型
**接口地址**: `/api/v1/audio/voice-models/{id}`

**请求方式**: `DELETE`

**请求头**: 需要认证

**路径参数**:
| 参数名 | 类型 | 说明 |
|-------|------|------|
| id | uuid | 模型ID |

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": null
}
```

---

## 7. 作品模块 API

### 7.1 获取作品列表
**接口地址**: `/api/v1/works`

**请求方式**: `GET`

**请求头**: 需要认证

**Query参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|-------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量 |
| status | string | 否 | - | 状态筛选 |
| work_type | string | 否 | - | 类型筛选 |
| sort | string | 否 | created_at | 排序字段 |
| order | string | 否 | desc | 排序方向 |

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "uuid",
        "title": "string",
        "work_type": "audio",
        "thumbnail_url": "string",
        "duration": 332,
        "status": "completed",
        "created_at": "datetime"
      }
    ],
    "total": 50,
    "page": 1,
    "page_size": 20,
    "total_pages": 3
  }
}
```

---

### 7.2 获取作品详情
**接口地址**: `/api/v1/works/{id}`

**请求方式**: `GET`

**请求头**: 需要认证

**路径参数**:
| 参数名 | 类型 | 说明 |
|-------|------|------|
| id | uuid | 作品ID |

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "uuid",
    "user_id": "uuid",
    "story_id": "uuid",
    "title": "string",
    "work_type": "audio",
    "file_url": "string",
    "thumbnail_url": "string",
    "duration": 332,
    "status": "completed",
    "settings": {
      "voice_type": "female",
      "speed": 1.0,
      "bg_music": "森林鸟鸣"
    },
    "created_at": "datetime",
    "updated_at": "datetime"
  }
}
```

---

### 7.3 导出作品
**接口地址**: `/api/v1/works/{id}/export`

**请求方式**: `GET`

**请求头**: 需要认证

**路径参数**:
| 参数名 | 类型 | 说明 |
|-------|------|------|
| id | uuid | 作品ID |

**Query参数**:
| 参数名 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| format | string | mp3 | 导出格式(mp3/wav/mp4) |

**响应**: 文件下载

---

### 7.4 生成分享链接
**接口地址**: `/api/v1/works/{id}/share`

**请求方式**: `POST`

**请求头**: 需要认证

**路径参数**:
| 参数名 | 类型 | 说明 |
|-------|------|------|
| id | uuid | 作品ID |

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "share_id": "string",
    "share_url": "string",
    "expires_at": "datetime"
  }
}
```

---

### 7.5 获取分享信息
**接口地址**: `/api/v1/works/shared/{share_id}`

**请求方式**: `GET`

**请求头**: 无需认证

**路径参数**:
| 参数名 | 类型 | 说明 |
|-------|------|------|
| share_id | string | 分享ID |

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "title": "string",
    "work_type": "audio",
    "file_url": "string",
    "thumbnail_url": "string",
    "duration": 332
  }
}
```

---

### 7.6 删除作品
**接口地址**: `/api/v1/works/{id}`

**请求方式**: `DELETE`

**请求头**: 需要认证

**路径参数**:
| 参数名 | 类型 | 说明 |
|-------|------|------|
| id | uuid | 作品ID |

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": null
}
```

---

## 8. AI任务模块 API

### 8.1 创建AI任务
**接口地址**: `/api/v1/ai/tasks`

**请求方式**: `POST`

**请求头**: 需要认证

**请求参数**:
```json
{
  "task_type": "string, 任务类型, 必填, 取值: synthesize/analyze/generate_image/compose_video",
  "story_id": "uuid, 故事ID, 必填",
  "params": {
    "voice_type": "string",
    "speed": 1.0,
    "pitch": 1.0
  }
}
```

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "uuid",
    "status": "pending",
    "created_at": "datetime"
  }
}
```

---

### 8.2 获取任务状态
**接口地址**: `/api/v1/ai/tasks/{task_id}`

**请求方式**: `GET`

**请求头**: 需要认证

**路径参数**:
| 参数名 | 类型 | 说明 |
|-------|------|------|
| task_id | uuid | 任务ID |

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "uuid",
    "task_type": "synthesize",
    "status": "processing",
    "progress": 60,
    "input_params": {},
    "result": null,
    "error_message": null,
    "started_at": "datetime",
    "completed_at": null,
    "created_at": "datetime"
  }
}
```

---

### 8.3 获取任务结果
**接口地址**: `/api/v1/ai/tasks/{task_id}/result`

**请求方式**: `GET`

**请求头**: 需要认证

**路径参数**:
| 参数名 | 类型 | 说明 |
|-------|------|------|
| task_id | uuid | 任务ID |

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "uuid",
    "task_type": "synthesize",
    "status": "success",
    "result": {
      "audio_url": "string",
      "duration": 332
    }
  }
}
```

---

### 8.4 取消任务
**接口地址**: `/api/v1/ai/tasks/{task_id}`

**请求方式**: `DELETE`

**请求头**: 需要认证

**路径参数**:
| 参数名 | 类型 | 说明 |
|-------|------|------|
| task_id | uuid | 任务ID |

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": null
}
```

---

### 8.5 获取任务历史
**接口地址**: `/api/v1/ai/tasks`

**请求方式**: `GET`

**请求头**: 需要认证

**Query参数**:
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|-------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量 |
| task_type | string | 否 | - | 任务类型筛选 |
| status | string | 否 | - | 状态筛选 |

**响应参数**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "task_id": "uuid",
        "task_type": "synthesize",
        "status": "success",
        "progress": 100,
        "created_at": "datetime",
        "completed_at": "datetime"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

---

## 9. 附录

### 9.1 状态枚举值

**故事状态 (story_status)**:
| 值 | 描述 |
|---|---|
| draft | 草稿 |
| published | 已发布 |

**作品类型 (work_type)**:
| 值 | 描述 |
|---|---|
| audio | 音频 |
| video | 视频 |

**任务状态 (task_status)**:
| 值 | 描述 |
|---|---|
| pending | 待处理 |
| processing | 处理中 |
| success | 成功 |
| failed | 失败 |

**声音类型 (voice_type)**:
| 值 | 描述 |
|---|---|
| female | 女声 |
| male | 男声 |
| child | 童声 |
| custom | 自定义 |

**声音模型状态 (model_status)**:
| 值 | 描述 |
|---|---|
| training | 训练中 |
| ready | 就绪 |
| failed | 失败 |

### 9.2 分类枚举值

**故事分类 (category)**:
| 值 | 描述 |
|---|---|
| 童话 | 童话故事 |
| 寓言 | 寓言故事 |
| 成语 | 成语故事 |
| 神话 | 神话传说 |
| 民间 | 民间故事 |

**目标年龄 (target_age)**:
| 值 | 描述 |
|---|---|
| 0-3岁 | 婴幼儿 |
| 3-6岁 | 学龄前 |
| 6-9岁 | 小学低年级 |
| 9-12岁 | 小学高年级 |

---

*文档版本：v1.0*
*创建日期：2026-04-12*
*最后更新：2026-04-12*
