# Tasks：Minecraft 服务端整合包制作应用

**输入**: [plan.md](./plan.md)、[spec.md](./spec.md)、[research.md](./research.md)、[data-model.md](./data-model.md)、[contracts/openapi.yaml](./contracts/openapi.yaml)

**测试**: 本任务清单包含测试任务，因为 plan 明确使用 pytest、Vitest、React Testing Library 和 API 合约测试。

**组织方式**: 任务按用户故事分组，保证每个故事可以独立实现、独立测试、独立演示。

## 格式：`[ID] [P?] [Story] 描述`

- **[P]**: 可并行执行，通常是不同文件且不依赖未完成任务。
- **[Story]**: 用户故事阶段任务必须标记，例如 `[US1]`。
- 每个任务都包含明确文件路径。

## Phase 1：项目初始化与基础结构

**目的**: 建立前端、后端、worker、部署和数据目录骨架。

- [x] T001 创建目录结构 `backend/app/`、`backend/tests/`、`frontend/src/`、`frontend/tests/`、`deploy/`、`data/uploads/`、`data/workspaces/`、`data/artifacts/`、`data/reports/`、`data/cache/`
- [x] T002 初始化后端 Python 项目配置 `backend/pyproject.toml`
- [x] T003 初始化前端 React + Vite + TypeScript 项目配置 `frontend/package.json`
- [x] T004 [P] 配置前端 TypeScript、Vite、Vitest、Tailwind 入口文件 `frontend/tsconfig.json`、`frontend/vite.config.ts`、`frontend/src/styles/index.css`
- [x] T005 [P] 配置后端 pytest 和测试路径 `backend/pytest.ini`
- [x] T006 创建 Docker Compose 和镜像文件 `deploy/docker-compose.yml`、`deploy/backend.Dockerfile`、`deploy/frontend.Dockerfile`、`deploy/worker.Dockerfile`
- [x] T007 创建环境变量示例和数据目录说明 `.env.example`、`data/README.md`

---

## Phase 2：基础设施与共享模型

**目的**: 完成所有用户故事共用的 API、数据库、任务队列、文件路径和 UI 基础设施。

**关键门禁**: 本阶段完成前，不开始任何用户故事实现。

- [x] T008 创建后端配置和路径管理 `backend/app/core/config.py`、`backend/app/core/paths.py`
- [x] T009 [P] 创建后端日志配置 `backend/app/core/logging.py`
- [x] T010 创建 SQLite 会话和数据库初始化 `backend/app/db/session.py`
- [x] T011 创建数据库模型 `backend/app/db/models.py`
- [x] T012 创建 Pydantic schema `backend/app/schemas/task.py`、`backend/app/schemas/pack.py`、`backend/app/schemas/source.py`、`backend/app/schemas/report.py`
- [x] T013 创建 RQ 队列连接和 worker 入口 `backend/app/workers/queue.py`、`backend/app/workers/jobs.py`
- [x] T014 创建 FastAPI 应用入口和健康检查路由 `backend/app/main.py`、`backend/app/api/routes_health.py`
- [x] T015 [P] 创建前端 API 客户端 `frontend/src/lib/api.ts`
- [x] T016 [P] 创建前端任务状态格式化工具 `frontend/src/lib/task-status.ts`、`frontend/src/lib/format.ts`
- [x] T017 [P] 创建基础 UI 组件目录和共享样式 `frontend/src/components/ui/`
- [x] T018 创建契约测试，验证后端路由满足 `specs/001-mc-server-app/contracts/openapi.yaml` 的核心路径 `backend/tests/contract/test_openapi_contract.py`
- [x] T019 创建任务状态 API 路由和近期任务路由 `backend/app/api/routes_tasks.py`

**检查点**: 后端可启动，健康检查可用，数据库和队列连接可初始化，前端能调用任务 API。

---

## Phase 3：用户故事 1 - 上传整合包生成服务端（P1）

**目标**: 用户上传 `.zip` 或 `.mrpack` 后，系统创建生成任务，分析整合包，隔离客户端专用 mod，生成服务端产物和中文报告。

**独立测试**: 使用 fixture 整合包上传，任务完成后能看到整合包识别信息、mod 决策、服务端产物或失败报告。

### 测试

- [x] T020 [P] [US1] 创建上传 API 集成测试 `backend/tests/integration/test_upload_generate_flow.py`
- [x] T021 [P] [US1] 创建压缩包安全校验单元测试 `backend/tests/unit/test_archive_security.py`
- [x] T022 [P] [US1] 创建服务端生成报告单元测试 `backend/tests/unit/test_report_builder.py`
- [x] T023 [P] [US1] 创建上传表单前端测试 `frontend/tests/upload-form.test.tsx`

### 实现

- [ ] T024 [P] [US1] 创建整合包 fixture `backend/tests/fixtures/packs/basic_mrpack/`
- [x] T025 [US1] 实现上传文件保存和基础校验服务 `backend/app/services/upload_storage.py`
- [x] T026 [US1] 实现上传并创建生成任务 API `backend/app/api/routes_uploads.py`
- [x] T027 [US1] 实现压缩包分析器，支持 `.zip` 与 `.mrpack` 基础 manifest 识别 `backend/app/services/archive_analyzer.py`
- [x] T028 [US1] 实现 jar 元数据读取和 mod 清单提取 `backend/app/services/mod_metadata.py`
- [x] T029 [US1] 实现 mod 端侧决策服务和本地规则入口 `backend/app/services/mod_decider.py`、`backend/app/services/rules/client_mods.json`
- [x] T030 [US1] 实现服务端目录生成和 `_disabled_client_mods/` 隔离 `backend/app/services/server_generator.py`
- [x] T031 [US1] 实现启动验证 runner，包含超时、日志截断和可开关配置 `backend/app/services/verification_runner.py`
- [x] T032 [US1] 实现中文报告生成 `backend/app/services/report_builder.py`
- [ ] T033 [US1] 连接 RQ 上传生成任务流程 `backend/app/workers/jobs.py`
- [x] T034 [P] [US1] 创建上传组件 `frontend/src/components/upload/UploadDropzone.tsx`
- [x] T035 [P] [US1] 创建生成模式表单 `frontend/src/components/upload/GenerateServerForm.tsx`
- [x] T036 [US1] 在首页集成上传生成入口 `frontend/src/pages/HomePage.tsx`

**检查点**: 上传生成故事可独立演示；即使启动验证失败，也能产出清晰中文失败报告。

---

## Phase 4：用户故事 2 - 自然语言查找官方服务端（P1）

**目标**: 用户输入自然语言后，系统识别整合包意图，检索 CurseForge、Modrinth、FTB，存在官方服务端则展示结果，不存在则明确说明。

**独立测试**: 使用 fixture 平台响应，验证“找到官方服务端”和“未找到官方服务端”两种结果。

### 测试

- [x] T037 [P] [US2] 创建自然语言解析单元测试 `backend/tests/unit/test_query_parser.py`
- [ ] T038 [P] [US2] 创建来源检索 fixture 响应 `backend/tests/fixtures/sources/`
- [x] T039 [P] [US2] 创建官方服务端检索集成测试 `backend/tests/integration/test_official_search_flow.py`
- [x] T040 [P] [US2] 创建自然语言检索前端测试 `frontend/tests/official-search.test.tsx`

### 实现

- [x] T041 [US2] 实现自然语言查询解析器 `backend/app/services/query_parser.py`
- [x] T042 [US2] 创建来源统一模型 `backend/app/sources/models.py`
- [x] T043 [P] [US2] 实现 Modrinth 来源客户端 `backend/app/sources/modrinth.py`
- [x] T044 [P] [US2] 实现 CurseForge 来源客户端和 API key 缺失处理 `backend/app/sources/curseforge.py`
- [x] T045 [P] [US2] 实现 FTB 来源客户端占位与不可用说明 `backend/app/sources/ftb.py`
- [x] T046 [US2] 实现官方服务端聚合检索服务 `backend/app/services/official_server_search.py`
- [x] T047 [US2] 实现自然语言检索任务 API `backend/app/api/routes_search.py`
- [ ] T048 [US2] 连接 RQ 官方服务端检索任务流程 `backend/app/workers/jobs.py`
- [x] T049 [P] [US2] 创建自然语言输入组件 `frontend/src/components/search/OfficialServerSearchForm.tsx`
- [x] T050 [P] [US2] 创建官方服务端候选列表组件 `frontend/src/components/search/OfficialServerCandidates.tsx`
- [x] T051 [US2] 在首页集成自然语言检索入口 `frontend/src/pages/HomePage.tsx`

**检查点**: 官方服务端检索故事可独立演示；未找到时必须显示已检索来源。

---

## Phase 5：用户故事 3 - 查看任务进度和结果（P2）

**目标**: 用户可以在任务页查看当前阶段、事件、结果产物、失败报告，并能下载服务端产物或报告。

**独立测试**: 创建任务后进入任务页，页面轮询任务状态并展示完成或失败结果。

### 测试

- [x] T052 [P] [US3] 创建任务详情 API 集成测试 `backend/tests/integration/test_task_detail_and_events.py`
- [x] T053 [P] [US3] 创建产物下载 API 集成测试 `backend/tests/integration/test_artifact_download.py`
- [x] T054 [P] [US3] 创建任务页前端测试 `frontend/tests/task-page.test.tsx`

### 实现

- [x] T055 [US3] 完善任务详情、任务事件和产物下载路由 `backend/app/api/routes_tasks.py`
- [x] T056 [US3] 实现任务事件写入辅助服务 `backend/app/services/task_events.py`
- [x] T057 [US3] 实现产物下载安全检查 `backend/app/services/artifact_access.py`
- [x] T058 [P] [US3] 创建任务阶段进度组件 `frontend/src/components/tasks/TaskProgress.tsx`
- [x] T059 [P] [US3] 创建任务事件列表组件 `frontend/src/components/tasks/TaskEventList.tsx`
- [x] T060 [P] [US3] 创建结果报告组件 `frontend/src/components/tasks/TaskResultReport.tsx`
- [x] T061 [US3] 创建任务详情页 `frontend/src/pages/TaskPage.tsx`
- [x] T062 [US3] 实现任务状态轮询和错误恢复 `frontend/src/lib/api.ts`

**检查点**: 用户可以不刷新页面查看任务推进，并能下载成功产物或复制失败报告。

---

## Phase 6：用户故事 4 - 管理历史结果和临时文件（P3）

**目标**: 用户查看近期任务；应用自动清理过期上传、工作区和产物，并在结果过期时给出中文说明。

**独立测试**: 构造未过期和已过期任务，验证历史页展示和清理行为。

### 测试

- [x] T063 [P] [US4] 创建清理服务单元测试 `backend/tests/unit/test_cleanup.py`
- [x] T064 [P] [US4] 创建历史任务 API 集成测试 `backend/tests/integration/test_task_history.py`
- [x] T065 [P] [US4] 创建历史页前端测试 `frontend/tests/history-page.test.tsx`

### 实现

- [x] T066 [US4] 实现过期任务和文件清理服务 `backend/app/services/cleanup.py`
- [x] T067 [US4] 实现清理任务 worker 入口 `backend/app/workers/jobs.py`
- [ ] T068 [US4] 完善近期任务 API 的过期状态展示 `backend/app/api/routes_tasks.py`
- [x] T069 [P] [US4] 创建近期任务列表组件 `frontend/src/components/tasks/RecentTasks.tsx`
- [x] T070 [US4] 创建历史任务页 `frontend/src/pages/HistoryPage.tsx`
- [x] T071 [US4] 在首页展示近期任务摘要 `frontend/src/pages/HomePage.tsx`

**检查点**: 历史结果可查看，过期结果不再提供下载且提示清晰。

---

## Phase 7：打磨与跨切面质量

**目的**: 完成部署、文档、可访问性、性能和安全收尾。

- [ ] T072 [P] 更新本地运行文档 `README.md`
- [ ] T073 [P] 将 quickstart 中的命令同步到 `README.md` 和 `.env.example`
- [ ] T074 验证 Docker Compose 启动前端、后端、worker、Redis `deploy/docker-compose.yml`
- [ ] T075 验证所有用户可见前端文案和后端错误信息均为简体中文 `frontend/src/`、`backend/app/`
- [ ] T076 验证未找到官方服务端时结果页列出 CurseForge、Modrinth、FTB `frontend/src/components/search/OfficialServerCandidates.tsx`
- [ ] T077 验证上传解压路径穿越防护和产物下载路径限制 `backend/app/services/archive_analyzer.py`、`backend/app/services/artifact_access.py`
- [ ] T078 优化来源检索缓存和任务状态查询性能 `backend/app/sources/`、`backend/app/api/routes_tasks.py`
- [ ] T079 执行前端无障碍检查，确保表单 label、键盘操作、`aria-live` 状态更新 `frontend/src/components/`
- [ ] T080 运行后端测试套件 `backend/tests/`
- [ ] T081 运行前端测试套件 `frontend/tests/`

---

## 依赖与执行顺序

### 阶段依赖

- **Phase 1 初始化**: 无依赖。
- **Phase 2 基础设施**: 依赖 Phase 1，阻塞所有用户故事。
- **Phase 3 上传生成服务端**: 依赖 Phase 2，是 MVP 的核心生成能力。
- **Phase 4 自然语言查找官方服务端**: 依赖 Phase 2，可与 Phase 3 并行开发。
- **Phase 5 任务进度和结果**: 依赖 Phase 2，最好在 Phase 3/4 基础流程可创建任务后完成。
- **Phase 6 历史结果和清理**: 依赖 Phase 5 的任务展示和产物模型。
- **Phase 7 打磨**: 依赖目标用户故事完成。

### 用户故事依赖

- **US1 上传整合包生成服务端**: 可在基础设施完成后独立交付。
- **US2 自然语言查找官方服务端**: 可在基础设施完成后独立交付。
- **US3 查看任务进度和结果**: 依赖任务 API，但可先用模拟任务数据实现。
- **US4 管理历史结果和临时文件**: 依赖任务和产物模型。

## 并行执行示例

### US1 并行

```text
T020 上传 API 集成测试
T021 压缩包安全校验单元测试
T022 服务端生成报告单元测试
T023 上传表单前端测试
T024 fixture 创建
T034 上传组件
T035 生成模式表单
```

### US2 并行

```text
T037 自然语言解析单元测试
T038 来源检索 fixture
T039 官方服务端检索集成测试
T040 前端检索测试
T043 Modrinth 来源客户端
T044 CurseForge 来源客户端
T045 FTB 来源客户端
T049 自然语言输入组件
T050 官方候选列表组件
```

### US3 并行

```text
T052 任务详情 API 集成测试
T053 产物下载 API 集成测试
T054 任务页前端测试
T058 任务阶段进度组件
T059 任务事件列表组件
T060 结果报告组件
```

## 实施策略

### MVP 优先

1. 完成 Phase 1 和 Phase 2。
2. 完成 US2 的官方服务端检索，因为它最符合“官方服务端优先”和最快反馈。
3. 完成 US1 的上传生成最小闭环，启动验证可以先做可开关。
4. 完成 US3 的任务页，让用户能看进度和结果。
5. 最后完成 US4 清理和历史页。

### 增量交付

1. 官方服务端检索可独立上线。
2. 上传分析可先输出报告，再加入服务端目录生成。
3. 启动验证可从“可选验证”逐步变为默认验证。
4. 清理策略和历史页在产物稳定后加入。
