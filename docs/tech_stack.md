# TaleVoice 技术选型文档

## 1. 文档概述

### 1.1 文档目的
本文档详细描述童话之声（TaleVoice）项目的技术选型依据、架构设计、技术栈详细说明以及第三方服务选型，为开发团队提供技术实现指南。

---

## 2. 技术架构总览

### 2.1 系统架构图
```
┌─────────────────────────────────────────────────────────────────┐
│                         客户端层                                │
│    ┌─────────────────┐         ┌─────────────────┐             │
│    │   Web浏览器      │         │   移动端H5      │             │
│    │   (Vue3)        │         │   (Vue3)        │             │
│    └─────────────────┘         └─────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         网关层                                   │
│    ┌─────────────────────────────────────────────────┐          │
│    │              Nginx / API Gateway                │          │
│    │         (负载均衡 / 静态资源服务 / SSL)          │          │
│    └─────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         服务层                                   │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐ │
│  │  Web服务   │  │  API服务   │  │  AI服务    │  │ 任务调度  │ │
│  │  (Vue3)   │  │  (Python)  │  │  (Python)  │  │ (Python)  │ │
│  └────────────┘  └────────────┘  └────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│    PostgreSQL   │  │      Redis      │  │    文件存储     │
│      数据库      │  │    缓存/队列    │  │   (本地/OSS)   │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 2.2 技术选型原则
| 原则 | 说明 |
|-----|------|
| 成熟稳定 | 选择主流技术栈，降低技术风险 |
| 团队熟悉 | 优先团队已有经验技术，提高效率 |
| 易于维护 | 完善的文档和社区支持 |
| 成本可控 | 考虑licence费用和运维成本 |
| 可扩展 | 架构支持横向扩展 |

---

## 3. 前端技术选型

### 3.1 核心框架
| 技术 | 版本 | 选型理由 |
|-----|------|---------|
| Vue.js | 3.x | 渐进式框架，易于上手，生态完善 |
| TypeScript | 5.x | 类型安全，提高代码质量 |
| Vite | 5.x | 开发体验好，构建速度快 |

### 3.2 UI框架
| 技术 | 版本 | 选型理由 |
|-----|------|---------|
| Element Plus | 2.x | Vue3生态成熟，组件丰富 |
| Ant Design Vue | 4.x | 企业级组件，设计规范 |

### 3.3 状态管理
| 技术 | 版本 | 选型理由 |
|-----|------|---------|
| Pinia | 2.x | Vue3官方推荐，轻量级 |

### 3.4 前端路由
| 技术 | 版本 | 选型理由 |
|-----|------|---------|
| Vue Router | 4.x | Vue官方路由管理 |

### 3.5 HTTP请求
| 技术 | 版本 | 选型理由 |
|-----|------|---------|
| Axios | 1.x | 功能完善，拦截器支持 |

### 3.6 前端工程化
| 技术 | 用途 |
|-----|------|
| ESLint | 代码规范检查 |
| Prettier | 代码格式化 |
| husky | Git hooks |

### 3.7 前端依赖清单
```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0",
    "axios": "^1.6.0",
    "element-plus": "^2.5.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "vite": "^5.0.0",
    "typescript": "^5.3.0",
    "eslint": "^8.56.0",
    "prettier": "^3.1.0"
  }
}
```

---

## 4. 后端技术选型

### 4.1 核心框架
| 技术 | 版本 | 选型理由 |
|-----|------|---------|
| Python | 3.11+ | AI友好，库丰富 |
| FastAPI | 0.109+ | 高性能，自动文档，类型安全 |
| Pydantic | 2.x | 数据验证，类型提示 |

### 4.2 Web框架（备选）
| 技术 | 版本 | 选型理由 |
|-----|------|---------|
| Flask | 3.x | 轻量灵活 |

### 4.3 ORM框架
| 技术 | 版本 | 选型理由 |
|-----|------|---------|
| SQLAlchemy | 2.x | 功能强大，兼容性好 |
| Alembic | 1.13+ | 数据库迁移管理 |

### 4.4 异步任务
| 技术 | 版本 | 选型理由 |
|-----|------|---------|
| Celery | 5.3+ | 分布式任务队列，成熟稳定 |
| Redis | 7.x | 消息队列+缓存双重角色 |

### 4.5 认证授权
| 技术 | 版本 | 选型理由 |
|-----|------|---------|
| JWT | - | 无状态认证 |
| Passlib | 1.7+ | 密码哈希 |

### 4.6 后端依赖清单
```txt
# requirements.txt
fastapi==0.109.2
uvicorn[standard]==0.27.1
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9
redis==5.0.1
celery==5.3.6
pydantic==2.6.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
aiofiles==23.2.1
httpx==0.26.0
```

---

## 5. 数据库选型

### 5.1 主数据库：PostgreSQL
| 指标 | 说明 |
|-----|------|
| 版本 | 15.x 或更高 |
| 部署方式 | Docker容器化部署 |
| 选型理由 | 关系型数据库，功能强大，扩展性好 |

#### 5.1.1 表结构设计

**用户表 (users)**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**故事表 (stories)**
```sql
CREATE TABLE stories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50),
    target_age VARCHAR(20),
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    word_count INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**作品表 (works)**
```sql
CREATE TABLE works (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    story_id UUID REFERENCES stories(id) ON DELETE SET NULL,
    title VARCHAR(200) NOT NULL,
    work_type VARCHAR(20) NOT NULL,
    file_url VARCHAR(500),
    thumbnail_url VARCHAR(500),
    duration INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'processing',
    settings JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**任务表 (tasks)**
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    input_params JSONB,
    result JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

**声音模型表 (voice_models)**
```sql
CREATE TABLE voice_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    model_url VARCHAR(500),
    sample_url VARCHAR(500),
    sample_duration INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'training',
    similarity FLOAT DEFAULT 0.8,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 5.2 缓存数据库：Redis
| 指标 | 说明 |
|-----|------|
| 版本 | 7.x |
| 用途 | Session存储、任务队列、缓存 |

#### 5.2.1 Key设计
```
# 用户Session
session:{user_id} → JSON

# 任务状态缓存
task:{task_id}:status → JSON

# 验证码
captcha:{uuid} → {code, expire}

# 限流
rate_limit:{user_id}:{action} → count
```

### 5.3 文件存储
| 存储类型 | 用途 | 说明 |
|---------|------|------|
| 本地存储 | 开发环境 | 开发测试用 |
| 阿里云OSS | 生产环境 | 海量存储，CDN加速 |

---

## 6. AI服务选型

### 6.1 语音合成服务
| 服务商 | 产品 | 选型理由 |
|-------|------|---------|
| 阿里云 | 智能语音交互 | 国产，延迟低，价格适中 |
| 腾讯云 | 语音合成 | 国产，质量稳定 |

**语音合成参数**
```python
TTS_CONFIG = {
    "provider": "aliyun",
    "app_id": os.getenv("ALIYUN_APP_ID"),
    "api_key": os.getenv("ALIYUN_API_KEY"),
    "voice_types": {
        "female": "xiaoyun",
        "male": "xiaowang",
        "child": "xiaoxian",
    },
    "default_speed": 1.0,
    "default_pitch": 1.0,
    "default_volume": 1.0,
}
```

### 6.2 配图生成服务
| 服务商 | 产品 | 选型理由 |
|-------|------|---------|
| OpenAI | DALL-E | 质量高，创意强 |
| Midjourney | - | 艺术感强 |

**图像生成参数**
```python
IMAGE_CONFIG = {
    "provider": "openai",
    "model": "dall-e-3",
    "size": "1024x1024",
    "quality": "standard",
}
```

### 6.3 大模型服务
| 服务商 | 产品 | 选型理由 |
|-------|------|---------|
| OpenAI | GPT-4 | 理解能力强 |
| 阿里云 | 通义千问 | 国产，性价比高 |

**LLM配置**
```python
LLM_CONFIG = {
    "provider": "aliyun",
    "model": "qwen-turbo",
    "api_key": os.getenv("DASHSCOPE_API_KEY"),
    "temperature": 0.7,
    "max_tokens": 2000,
}
```

---

## 7. 第三方服务汇总

| 服务类别 | 服务商 | 产品 | 用途 |
|---------|-------|------|------|
| 云服务 | 阿里云 | ECS/VPC | 基础设施 |
| 数据库 | 阿里云 | RDS PostgreSQL | 主数据库 |
| 缓存 | 阿里云 | Redis | 缓存/队列 |
| 对象存储 | 阿里云 | OSS | 文件存储 |
| CDN | 阿里云 | CDN | 静态资源加速 |
| 域名 | - | - | 域名解析 |
| SSL | Let's Encrypt | - | HTTPS证书 |
| 短信 | 阿里云 | SMS | 短信验证码 |
| 邮箱 | SendGrid | - | 邮件发送 |

---

## 8. 开发工具选型

### 8.1 开发环境
| 工具 | 说明 |
|-----|------|
| IDE | VS Code / PyCharm |
| Git | 版本控制 |
| Docker | 容器化开发 |
| Postman/Apifox | API调试 |

### 8.2 测试工具
| 工具 | 说明 |
|-----|------|
| pytest | Python单元测试 |
| Vitest | 前端单元测试 |
| Selenium | E2E测试 |

### 8.3 部署工具
| 工具 | 说明 |
|-----|------|
| Docker | 容器化部署 |
| Docker Compose | 本地开发环境 |
| Nginx | 反向代理/静态服务 |

### 8.4 监控工具
| 工具 | 说明 |
|-----|------|
| Sentry | 错误监控 |
| Prometheus | 指标采集 |
| Grafana | 可视化展示 |

---

## 9. 项目目录结构

### 9.1 后端目录结构
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # 应用入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── dependencies.py      # 依赖注入
│   │
│   ├── api/                 # API层
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py       # 认证接口
│   │   │   ├── users.py     # 用户接口
│   │   │   ├── stories.py    # 故事接口
│   │   │   ├── audio.py      # 语音接口
│   │   │   ├── works.py      # 作品接口
│   │   │   └── tasks.py      # 任务接口
│   │   └── router.py        # 路由汇总
│   │
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── story.py
│   │   ├── work.py
│   │   ├── task.py
│   │   └── voice_model.py
│   │
│   ├── schemas/             # Pydantic模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── story.py
│   │   ├── work.py
│   │   ├── task.py
│   │   └── voice_model.py
│   │
│   ├── services/            # 业务逻辑
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── story_service.py
│   │   ├── audio_service.py
│   │   ├── ai_service.py
│   │   └── task_service.py
│   │
│   ├── core/                # 核心模块
│   │   ├── __init__.py
│   │   ├── security.py      # 安全认证
│   │   ├── exceptions.py    # 异常定义
│   │   └── utils.py         # 工具函数
│   │
│   └── tasks/               # 异步任务
│       ├── __init__.py
│       ├── celery_app.py    # Celery配置
│       ├── synthesize.py    # 语音合成任务
│       └── generate.py      # 配图生成任务
│
├── tests/                   # 测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── api/
│   └── services/
│
├── scripts/                 # 脚本
│   ├── init_db.py
│   └── seed_data.py
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### 9.2 前端目录结构
```
frontend/
├── public/
│   └── index.html
│
├── src/
│   ├── __init__.py
│   ├── main.ts              # 入口文件
│   ├── App.vue              # 根组件
│   │
│   ├── assets/              # 静态资源
│   │   ├── images/
│   │   └── styles/
│   │
│   ├── components/           # 公共组件
│   │   ├── common/
│   │   ├── story/
│   │   ├── audio/
│   │   └── work/
│   │
│   ├── views/                # 页面组件
│   │   ├── auth/
│   │   │   ├── Login.vue
│   │   │   └── Register.vue
│   │   ├── story/
│   │   │   ├── StoryList.vue
│   │   │   ├── StoryDetail.vue
│   │   │   └── StoryEdit.vue
│   │   ├── audio/
│   │   │   ├── AudioGenerate.vue
│   │   │   └── VoiceModels.vue
│   │   ├── work/
│   │   │   ├── WorkList.vue
│   │   │   └── WorkDetail.vue
│   │   └── user/
│   │       └── Profile.vue
│   │
│   ├── router/               # 路由配置
│   │   └── index.ts
│   │
│   ├── stores/                # 状态管理
│   │   ├── user.ts
│   │   ├── story.ts
│   │   └── work.ts
│   │
│   ├── services/              # API服务
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   ├── story.ts
│   │   ├── audio.ts
│   │   └── work.ts
│   │
│   ├── types/                 # TypeScript类型
│   │   ├── user.ts
│   │   ├── story.ts
│   │   ├── audio.ts
│   │   └── work.ts
│   │
│   └── utils/                 # 工具函数
│       ├── request.ts
│       ├── storage.ts
│       └── validate.ts
│
├── package.json
├── vite.config.ts
├── tsconfig.json
├── eslint.config.js
└── README.md
```

---

## 10. 安全设计

### 10.1 认证机制
- JWT Token认证
- Token有效期：Access Token 2小时，Refresh Token 7天
- Token存储：HttpOnly Cookie 或 LocalStorage

### 10.2 授权机制
- RBAC基于角色的访问控制
- 角色：超级管理员、管理员、普通用户

### 10.3 安全措施
| 措施 | 说明 |
|-----|------|
| 密码加密 | bcrypt哈希 |
| SQL注入防护 | ORM参数化查询 |
| XSS防护 | 输入输出转义 |
| CSRF防护 | Token验证 |
| 请求限流 | Redis计数器 |
| 敏感数据加密 | AES加密 |

---

## 11. 性能优化策略

### 11.1 前端优化
- 路由懒加载
- 组件按需引入
- 图片懒加载
- Gzip压缩

### 11.2 后端优化
- 数据库索引优化
- Redis缓存热点数据
- 异步任务处理
- 连接池复用

### 11.3 数据库优化
```sql
-- 故事表索引
CREATE INDEX idx_stories_user_id ON stories(user_id);
CREATE INDEX idx_stories_status ON stories(status);
CREATE INDEX idx_stories_created_at ON stories(created_at DESC);

-- 作品表索引
CREATE INDEX idx_works_user_id ON works(user_id);
CREATE INDEX idx_works_status ON works(status);

-- 任务表索引
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);
```

---

## 12. 部署架构

### 12.1 开发环境
```
开发者PC
    │
    ├── Docker Compose (PostgreSQL + Redis)
    │
    └── 运行前端 + 后端服务
```

### 12.2 生产环境
```
                    ┌─────────────┐
                    │   Nginx     │
                    │  (负载均衡) │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
  ┌───────────┐    ┌───────────┐    ┌───────────┐
  │  API Server │    │  API Server │    │  API Server │
  │   (Node1)   │    │   (Node2)   │    │   (Node3)   │
  └─────┬──────┘    └─────┬──────┘    └─────┬──────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
  ┌───────────┐    ┌───────────┐    ┌───────────┐
  │ PostgreSQL │    │   Redis   │    │    OSS    │
  │   Master   │    │  Cluster  │    │  (Storage)│
  └───────────┘    └───────────┘    └───────────┘
```

### 12.3 Docker配置

**docker-compose.yml**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: talevoice
      POSTGRES_USER: talevoice
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://talevoice:${DB_PASSWORD}@postgres:5432/talevoice
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis

  web:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - api

volumes:
  postgres_data:
  redis_data:
```

---

*文档版本：v1.0*
*创建日期：2026-04-12*
*最后更新：2026-04-12*
