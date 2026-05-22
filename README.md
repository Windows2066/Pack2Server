# Minecraft 服务端整合包制作应用

这是一个面向个人使用的 Web 工具，用来从 Minecraft 客户端整合包快速查找官方服务端，或在未找到官方服务端时生成本地服务端基础产物。

## 功能范围

- 上传 `.zip` 或 `.mrpack`，创建服务端生成任务。
- 使用自然语言描述整合包，检索 CurseForge、Modrinth、FTB 是否有官方服务端。
- 查看任务状态、进度事件、基础分析结果和中文报告。
- 保留原始上传文件，将临时数据写入本地 `data/`。

## 技术栈

- 前端：React + Vite + TypeScript
- 后端：FastAPI + Pydantic + SQLAlchemy
- 任务：RQ + Redis，当前 MVP 默认 `RUN_JOBS_INLINE=true` 以便本地直接可用
- 存储：SQLite + 本地文件目录
- 部署：Docker Compose

## 本地启动

使用 Docker Compose：

```powershell
docker compose -f deploy/docker-compose.yml up --build
```

启动后访问：

```text
http://localhost:5173
```

后端 API：

```text
http://localhost:8000
```

## 环境变量

复制 `.env.example` 后按需调整：

```text
APP_ENV=development
DATA_DIR=./data
DATABASE_URL=sqlite:///./data/app.db
REDIS_URL=redis://redis:6379/0
MAX_UPLOAD_BYTES=2147483648
ARTIFACT_RETENTION_HOURS=72
ENABLE_STARTUP_VERIFICATION=false
RUN_JOBS_INLINE=true
USE_FIXTURES=true
CURSEFORGE_API_KEY=
```

`RUN_JOBS_INLINE=true` 适合本地和当前 MVP；后续任务状态完全落到 SQLite 后，可以切换为 RQ worker 异步执行。

## 开发验证

后端：

```powershell
cd backend
python -m pytest
```

前端：

```powershell
cd frontend
npm.cmd test
npm.cmd run build
```

## 数据目录

```text
data/
├── uploads/      # 原始上传
├── workspaces/   # 解压和处理工作区
├── artifacts/    # 服务端产物
├── reports/      # 中文报告和日志摘录
└── cache/        # 平台响应和端侧规则缓存
```

默认产物保留 72 小时。过期任务在近期任务 API 中显示为“已过期”。

## 当前限制

- 官方来源客户端仍是 fixture/占位级实现，真实 API 细节需要继续补齐。
- RQ 入口已经接入，但当前 MVP 默认内联执行；跨进程 worker 状态持久化需要后续接入 SQLite 任务仓库。
- 服务端生成目前完成基础整合包分析和报告，还未生成完整可运行服务端压缩包。
