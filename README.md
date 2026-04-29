# TaleVoice
一款讲童话故事的软件

## 后端启动步骤

### 1. 安装依赖

首先，确保已安装Python 3.12和Pip。然后，导航到后端项目目录并安装依赖：

```bash
cd TaleVoice/backend
pip install -r requirements.txt
```

### 2. 配置环境变量

将`.env.example`文件复制为`.env`，并根据实际情况修改配置项。

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑.env文件，设置数据库连接、JWT密钥等
```

### 3. 启动后端
```bash
uvicorn main:app --reload
```
