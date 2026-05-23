# Minecraft 服务端整合包制作应用

这是一个面向个人使用的 Web 工具，用来从 Minecraft 客户端整合包快速查找官方服务端，或在未找到官方服务端时生成本地服务端基础产物。

## 功能范围

- 上传 `.zip` 或 `.mrpack`，创建服务端生成任务。
- 使用自然语言描述整合包，检索 CurseForge、Modrinth、FTB 是否有官方服务端。
- 查看任务状态、进度事件、中文报告，并下载生成的服务端压缩包。
- 生成产物包含启动脚本、`VERIFICATION.md`、隔离的客户端专用 mod 和可选启动验证结果。
- 保留原始上传文件，将临时数据写入本地 `data/`。

## 技术栈

- 前端：React + Vite + TypeScript
- 后端：FastAPI + Pydantic + SQLAlchemy
- 任务：RQ + Redis，当前 MVP 默认 `RUN_JOBS_INLINE=true` 以便本地直接可用
- 存储：SQLite + 本地文件目录
- 部署：Docker Compose 作为二期服务器搭建内容，当前一期不作为验收门槛

## 本地启动

后端：

```powershell
cd backend
python -m pip install -e .[dev]
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

前端另开一个终端：

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

启动后访问前端：

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
REDIS_URL=redis://localhost:6379/0
MAX_UPLOAD_BYTES=2147483648
ARTIFACT_RETENTION_HOURS=72
ENABLE_STARTUP_VERIFICATION=false
RUN_JOBS_INLINE=true
USE_FIXTURES=true
REMOTE_MOD_DOWNLOAD_WORKERS=8
CURSEFORGE_API_KEY=
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
```

`RUN_JOBS_INLINE=true` 适合本地调试；此模式下不需要先启动 Redis。改为 `false` 后，API 只创建任务并写入 SQLite，
实际执行交给 RQ worker。任务状态、事件、报告和产物元数据会持久化到 SQLite，后端重启后仍可查询。

异步 worker 示例：

```powershell
cd backend
rq worker default --url redis://localhost:6379/0
```

`ENABLE_STARTUP_VERIFICATION=false` 时会生成验证报告并明确标记“启动验证已跳过”。改为
`true` 后，后端会在工作区执行 `java -Xms1G -Xmx2G -jar server.jar nogui`，捕获 ready
日志；如果未找到 `server.jar` 或进程未进入 ready 状态，任务会返回启动验证失败报告。

`USE_FIXTURES=true` 会使用本地样例结果，适合开发和测试。要执行真实官方来源检索，将它改为
`USE_FIXTURES=false`；CurseForge 真实检索还需要配置 `CURSEFORGE_API_KEY`。

`REMOTE_MOD_DOWNLOAD_WORKERS` 控制从整合包 manifest 下载远程 mod 时的并发线程数。默认 `8`，
本地网络较好时可以适当调高；如果遇到平台限流或连接失败，可以调低。

`DEEPSEEK_API_KEY` 用于复杂自然语言解析和候选整合包识别。未配置时会自动回退到本地规则解析。
不要把真实 key 写入仓库；`.env`、`.env.*`、`*.env`、`*.key` 和 `secrets/` 已被 `.gitignore` 忽略。

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

- 官方来源客户端已接入真实检索路径：Modrinth 使用公开 API，CurseForge 需要 API key，FTB 使用官方 Server Files 页面提取安装器链接。开发测试仍默认保留 fixture 模式。
- RQ 入口已经接入；默认仍可内联执行，改为 `RUN_JOBS_INLINE=false` 后可以使用 Redis + RQ worker 异步处理。
- 服务端生成会产出可下载压缩包；loader/server jar 自动安装仍是后续增强项，当前需要用户按 `INSTALL.md` 放入匹配的 `server.jar` 后再执行真实启动验证。
- Docker Compose 文件已保留在 `deploy/`，但服务器部署和镜像拉取问题放到二期处理。
