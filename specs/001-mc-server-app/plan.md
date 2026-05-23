# 实施计划：Minecraft 服务端整合包制作应用

> 本文档正文、说明、用户可见提示和验收描述使用简体中文。代码标识符、命令、
> 路径、第三方名称、协议字段和日志原文保留原语言。

**分支**: `001-mc-server-app` | **日期**: 2026-05-22 | **规格**: [spec.md](./spec.md)

**输入**: 来自 [specs/001-mc-server-app/spec.md](./spec.md) 的功能规格；用户指定技术栈：
React + Vite + TypeScript + ui-ux-pro-max、FastAPI + RQ + Redis、SQLite +
本地文件存储。Docker Compose 保留为二期服务器部署内容。

## 摘要

实现一个前后端分离的 Web 工具。用户可以上传 Minecraft 客户端整合包压缩包，
由后台任务分析并生成服务端目录；也可以用自然语言描述想要的整合包服务端，
系统先检索 CurseForge、Modrinth、FTB 是否存在官方服务端，存在则优先提供，
不存在则明确说明“未找到官方服务端”并列出已检索来源。

第一版采用本地运行优先：前端通过 Vite dev server 提供上传、自然语言输入、任务进度和结果页；
FastAPI 提供 REST API；任务默认通过 `RUN_JOBS_INLINE=true` 在本地内联执行，避免一期依赖
Redis 和 Docker；SQLite 记录任务、证据和结果；本地 `data/` 目录保存上传、工作区、产物、
报告和缓存。Docker Compose、独立 Redis worker 和服务器长期运行配置放到二期。

## 技术上下文

**语言/版本**: 前端 TypeScript；后端 Python 3.12；运行验证使用 Java 17/21。

**主要依赖**: React、Vite、Tailwind CSS、shadcn/ui 风格组件、lucide-react、FastAPI、
Pydantic、SQLAlchemy、RQ、Redis、httpx、tomli/tomllib、python-multipart、pytest。

**存储**: SQLite 保存结构化任务数据；本地文件系统保存上传包、工作区、生成产物、
报告和来源缓存。

**测试**: 前端使用 Vitest + React Testing Library；后端使用 pytest；API 合约以
OpenAPI 文件和后端测试验证；任务处理使用 fixture 包和缓存响应测试。

**目标平台**: 一期目标为 Windows 本地开发环境；二期目标为 Linux 服务器上的 Docker Compose。

**项目类型**: 前后端 Web 应用 + 后台 worker + 本地文件处理工具。

**性能目标**:

- 明确自然语言官方服务端检索在 30 秒内返回结果或失败原因。
- 单机 MVP 同时运行 1 个上传生成任务和 1 个官方检索任务。
- 任务状态查询接口响应时间在本机运行下保持 500ms 内。
- 生成任务进度至少在每个关键阶段更新一次。

**约束**:

- v1 默认最大上传文件 2GB，具体可通过配置调整。
- v1 默认单个生成/验证任务最长 30 分钟，启动验证最长 15 分钟。
- v1 默认产物保留 72 小时，过期后自动清理上传包、工作区和生成产物。
- v1 不实现账号、计费、公开市场或公共 mod 二次分发。
- v1 对外部平台访问必须支持 fixture 或缓存模式，避免测试依赖实时网络。

**规模/范围**: 面向个人或少量用户；一期本地运行；任务串行或低并发；后续可演进到
Docker Compose、PostgreSQL、对象存储和多 worker。

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

**结构决策**: 使用前后端分离结构。前端和后端独立测试；一期默认内联执行任务，worker
代码保留为后续独立进程入口；`data/` 作为本地持久化目录。`deploy/` 中的 Docker 文件保留，
但不纳入一期验收。

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

## 增量设计：mod 端侧证据链判定器

**目标**: 替换当前仅按文件名命中客户端规则的粗略实现，生成服务端时按证据优先级
判断每个 mod 应保留、隔离或标记不确定，并在用户可见报告中解释原因。

**证据优先级**:

1. **平台元数据**：CurseForge 项目/文件元数据优先，其次是 Modrinth
   `client_side/server_side`；整合包 manifest 中能关联的平台项目和文件信息必须作为证据记录。
2. **jar 内元数据**：`fabric.mod.json`、`quilt.mod.json`、`META-INF/mods.toml`、
   `META-INF/neoforge.mods.toml`。Fabric/Quilt 的 `environment=client` 可作为客户端专用强证据。
3. **Modrinth hash lookup**：对已下载或本地已有 jar 计算 SHA1，通过
   `POST /v2/version_files` 反查 Modrinth 项目，再读取 `client_side/server_side`；
   该证据用于补足没有 manifest 项目标识、CurseForge 下载文件和用户直接放入 `mods/` 的 jar。
4. **MCMod 运行环境信息**：通过缓存 provider 读取“客户端/服务端安装需求”，不可用时降级。
5. **Mixin 启发式**：读取根目录 `*.mixins.json`，当只有 `client` mixin 且没有 common
   `mixins` 时，作为低优先级客户端倾向证据；不得单独覆盖明确平台或 MCMod 服务端证据。
6. **本地维护规则**：内置结构化规则和 `data/rules/local_mod_side_rules.json` 用户确认规则。

**Modrinth 端侧规则**:

- 采用 DeEarthX `ModrinthFilter` 的客户端判断语义：`client_side=required`
  或 `client_side=optional` 且 `server_side=unsupported` 时，判定为客户端专用候选。
- 为了服务端生成安全性，本项目额外保留服务端强证据：`server_side=required` 或
  `server_side=optional` 时判定为 `keep_server`，并在与客户端规则冲突时输出
  `needs_review`，默认保留 mod。

**MCMod provider 与 DeepSeek 取舍**:

- MCMod provider 第一版只解析结构化运行环境文本，映射到
  `服务端需装`、`服务端可选`、`服务端无效`、`客户端需装`、`客户端可选`、`客户端无效`。
- DeepSeek 不作为默认判定器接入端侧决策。只有当 MCMod 页面存在多义文本、候选搜索结果
  无法稳定匹配，或多个证据冲突需要生成中文解释时，才作为可选辅助解释器使用。
- DeepSeek 输出不得直接成为强证据；它只能生成 `needs_review` 说明或候选规则建议，
  必须保留原始 MCMod/平台/jar 证据引用。

**交付分层**:

- 第一批实现：结构化本地规则、Fabric/Quilt jar 元数据、决策报告落盘，补齐
  Xaero's World Map、Tweakerge、Tweakeroo 等规则。
- 第二批实现：接入 CurseForge 和 Modrinth 平台元数据；当两者都有证据时，
  CurseForge 优先级高于 Modrinth。
- 第三批实现：实现 MCMod provider、缓存和不可用降级，并评估 DeepSeek 仅作为
  解释/歧义辅助，不进入默认强判定链。
- 第四批实现：实现 Modrinth hash lookup，覆盖没有 manifest 项目标识的本地 jar。
- 第五批实现：实现 Mixin 启发式，作为低优先级弱证据补充。
- 第六批实现：从启动失败日志或用户确认操作生成候选规则，并提供确认后写入本地规则的入口。

**风险与约束**:

- 端侧误判会影响服务端可运行性，因此所有弱证据默认保留，不自动删除。
- MCMod 只能作为辅助证据，页面结构变化或访问失败不能阻塞生成。
- DeepSeek 可能产生幻觉或过度解释，不能替代可追溯来源证据。
- Mixin 启发式容易误伤同时包含客户端显示和服务端逻辑的 mod，只能作为低置信度证据。
- 本地自扩展规则必须保留用户确认边界，避免系统偷偷学习出破坏性规则。
