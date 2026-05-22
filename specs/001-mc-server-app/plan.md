# 实施计划：Minecraft 服务端整合包制作应用

> 本文档正文、说明、用户可见提示和验收描述使用简体中文。代码标识符、命令、
> 路径、第三方名称、协议字段和日志原文保留原语言。

**分支**: `001-mc-server-app` | **日期**: 2026-05-22 | **规格**: [spec.md](./spec.md)

**输入**: 来自 [specs/001-mc-server-app/spec.md](./spec.md) 的功能规格；用户指定技术栈：
React + Vite + TypeScript + ui-ux-pro-max、FastAPI + RQ + Redis、SQLite +
本地文件存储、Docker Compose。

## 摘要

实现一个前后端分离的 Web 工具。用户可以上传 Minecraft 客户端整合包压缩包，
由后台任务分析并生成服务端目录；也可以用自然语言描述想要的整合包服务端，
系统先检索 CurseForge、Modrinth、FTB 是否存在官方服务端，存在则优先提供，
不存在则明确说明“未找到官方服务端”并列出已检索来源。

第一版采用单机 Docker Compose 部署：前端负责上传、自然语言输入、任务进度和结果页；
FastAPI 提供 REST API；RQ worker 执行检索、解压、分析、生成和启动验证；Redis
承载任务队列；SQLite 记录任务、证据和结果；本地 `data/` 目录保存上传、工作区、
产物、报告和缓存。

## 技术上下文

**语言/版本**: 前端 TypeScript；后端 Python 3.12；运行验证使用 Java 17/21。

**主要依赖**: React、Vite、Tailwind CSS、shadcn/ui 风格组件、lucide-react、FastAPI、
Pydantic、SQLAlchemy、RQ、Redis、httpx、tomli/tomllib、python-multipart、pytest。

**存储**: SQLite 保存结构化任务数据；本地文件系统保存上传包、工作区、生成产物、
报告和来源缓存。

**测试**: 前端使用 Vitest + React Testing Library；后端使用 pytest；API 合约以
OpenAPI 文件和后端测试验证；任务处理使用 fixture 包和缓存响应测试。

**目标平台**: Linux 服务器上的 Docker Compose；本地开发支持 Windows + Docker Desktop
或 WSL2。

**项目类型**: 前后端 Web 应用 + 后台 worker + 本地文件处理工具。

**性能目标**:

- 明确自然语言官方服务端检索在 30 秒内返回结果或失败原因。
- 单机 MVP 同时运行 1 个上传生成任务和 1 个官方检索任务。
- 任务状态查询接口响应时间在本机或单机部署下保持 500ms 内。
- 生成任务进度至少在每个关键阶段更新一次。

**约束**:

- v1 默认最大上传文件 2GB，具体可通过配置调整。
- v1 默认单个生成/验证任务最长 30 分钟，启动验证最长 15 分钟。
- v1 默认产物保留 72 小时，过期后自动清理上传包、工作区和生成产物。
- v1 不实现账号、计费、公开市场或公共 mod 二次分发。
- v1 对外部平台访问必须支持 fixture 或缓存模式，避免测试依赖实时网络。

**规模/范围**: 面向个人或少量用户；单机部署；任务串行或低并发；后续可演进到
PostgreSQL、对象存储和多 worker。

## 宪法检查

*门禁：Phase 0 research 前必须通过；Phase 1 design 后必须重新检查。*

- **官方服务端优先**：通过自然语言检索流程和 `source_clients` 设计，先查
  CurseForge、Modrinth、FTB；未找到时固定展示“未找到官方服务端”，并列出已检索来源。
- **快速且有引导的用户流程**：前端首屏提供两个明确入口：上传生成、自然语言查找。
  默认选项隐藏专家细节，进度以“上传校验、来源检索、整合包分析、服务端生成、启动验证”
  展示。
- **基于证据的来源解析**：所有查询、端侧判断、生成和验证结果写入 `evidence_records`，
  报告引用证据摘要。
- **安全生成与运行验证**：原始上传保留在 `data/uploads/`，客户端专用 mod 移到
  `_disabled_client_mods/`；启动验证通过 worker 子进程执行，保存日志摘录。
- **可复用知识与透明边界**：来源响应和端侧规则写入本地缓存；报告展示缓存时间、
  来源不可用、限流和不支持格式。
- **中文统一**：所有 UI 文案、API 错误、报告、quickstart、contracts 描述使用中文。

复查结果：当前设计满足宪法门禁，无需复杂性例外。

## 项目结构

### 文档

```text
specs/001-mc-server-app/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
└── checklists/
    └── requirements.md
```

### 源码

```text
backend/
├── app/
│   ├── api/
│   │   ├── routes_health.py
│   │   ├── routes_tasks.py
│   │   ├── routes_uploads.py
│   │   └── routes_search.py
│   ├── core/
│   │   ├── config.py
│   │   ├── paths.py
│   │   └── logging.py
│   ├── db/
│   │   ├── models.py
│   │   ├── session.py
│   │   └── migrations/
│   ├── schemas/
│   │   ├── task.py
│   │   ├── pack.py
│   │   ├── source.py
│   │   └── report.py
│   ├── services/
│   │   ├── archive_analyzer.py
│   │   ├── server_generator.py
│   │   ├── verification_runner.py
│   │   ├── report_builder.py
│   │   └── cleanup.py
│   ├── sources/
│   │   ├── curseforge.py
│   │   ├── modrinth.py
│   │   ├── ftb.py
│   │   └── models.py
│   ├── workers/
│   │   ├── jobs.py
│   │   └── queue.py
│   └── main.py
├── tests/
│   ├── contract/
│   ├── integration/
│   ├── unit/
│   └── fixtures/
└── pyproject.toml

frontend/
├── src/
│   ├── app/
│   ├── components/
│   │   ├── upload/
│   │   ├── search/
│   │   ├── tasks/
│   │   └── ui/
│   ├── lib/
│   │   ├── api.ts
│   │   ├── format.ts
│   │   └── task-status.ts
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── TaskPage.tsx
│   │   └── HistoryPage.tsx
│   └── styles/
├── tests/
└── package.json

deploy/
├── docker-compose.yml
├── backend.Dockerfile
├── frontend.Dockerfile
└── worker.Dockerfile

data/
├── uploads/
├── workspaces/
├── artifacts/
├── reports/
└── cache/
```

**结构决策**: 使用前后端分离结构。前端和后端独立测试、独立镜像；worker 复用
后端业务代码但以独立进程运行；`data/` 作为本地持久化卷。

## UI/UX 设计方案

基于 `ui-ux-pro-max` 的规则，本应用采用“工具型工作台”而不是营销页。首屏直接
展示两个任务入口和最近任务，不做落地页式 hero。

- **信息架构**：顶部标题区 + 双模式分段控件 + 当前任务/最近任务列表。
- **视觉风格**：克制、清晰、偏开发工具质感；浅色默认，预留暗色 token；避免大面积
  单色渐变和装饰性背景。
- **组件规范**：按钮、上传区、候选项、任务状态、错误报告使用稳定尺寸；图标使用
  lucide-react；不使用 emoji 作为结构图标。
- **交互反馈**：上传和提交按钮必须有 loading/disabled 状态；错误信息显示在相关区域；
  长任务使用阶段进度条和日志摘要，不只显示 spinner。
- **无障碍**：所有表单有可见 label；按钮和上传区支持键盘操作；状态更新区域使用
  `aria-live="polite"`；颜色不作为唯一状态表达。
- **响应式**：移动端单列，桌面端双栏；任务结果报告优先可读性，限制正文行宽。

## 复杂性跟踪

无宪法违反项。
