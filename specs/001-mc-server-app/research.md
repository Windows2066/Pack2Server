# Research：Minecraft 服务端整合包制作应用

## 决策：前端使用 React + Vite + TypeScript

**理由**: 项目需要一个响应迅速的工具型 Web 界面，核心是上传、自然语言输入、
任务进度、候选项选择和结果报告。React 生态成熟，TypeScript 有利于维护 API
类型，Vite 适合轻量快速的前端开发。

**备选方案**:

- Next.js：全栈能力强，但本项目后端长任务和文件处理更适合独立 FastAPI。
- Vue + Vite：可行，但当前选择 React 便于搭配 shadcn/ui 风格组件和成熟测试生态。
- SvelteKit：轻量，但生态和后续协作资料相对少。

## 决策：UI 采用 ui-ux-pro-max 指导下的工具型工作台设计

**理由**: 应用服务的是重复使用的操作流程，不是品牌展示页。界面必须高密度但不拥挤，
清楚展示任务入口、任务进度、候选项和失败报告。设计重点是无障碍、表单反馈、
进度可见、状态清晰、移动端可用。

**备选方案**:

- 营销页式布局：不适合，用户打开后需要直接完成任务。
- 重后台布局：当前功能少，完整 sidebar 会显得过重。
- 游戏化视觉：和工具任务不匹配，容易牺牲可读性。

## 决策：后端使用 FastAPI

**理由**: FastAPI 适合构建清晰的 REST API，Pydantic 模型能直接表达任务、候选项、
报告和错误结构。Python 对 zip/mrpack 解析、jar 元数据读取、HTTP 检索、日志处理、
子进程启动验证都比较顺手。

**备选方案**:

- NestJS：工程化强，但处理压缩包、Java 子进程和 Python 生态工具不如 FastAPI 直接。
- Go：部署简单、并发好，但快速迭代解析逻辑和报告生成成本更高。
- Spring Boot：稳定但对个人 MVP 过重。

## 决策：后台任务使用 RQ + Redis

**理由**: 上传生成和启动验证是长任务，不能阻塞 API 请求。RQ 模型简单，足够支持
任务入队、worker 执行、失败重试和状态追踪。Redis 同时作为队列后端，部署简单。

**备选方案**:

- FastAPI BackgroundTasks：过于轻量，进程重启时任务可靠性不足。
- Celery：功能强，但对 MVP 偏重。
- Dramatiq：可行，但 RQ 更直观，降低个人项目维护成本。

## 决策：SQLite + 本地文件存储作为 v1 持久化

**理由**: v1 面向个人或少量用户，SQLite 足够保存任务、证据、候选项和报告元数据；
本地文件系统适合保存大体积上传包、工作区、生成产物和缓存。这个组合部署最简单，
符合单机 Docker Compose 起步目标。

**备选方案**:

- PostgreSQL：适合多 worker/多人使用，作为后续升级路径。
- 对象存储：适合公网下载和长期保存，v1 先不引入额外云依赖。
- Redis-only：不适合保存任务历史和结构化报告。

## 决策：服务端启动验证由 worker 子进程执行，后续可替换 Docker 沙箱

**理由**: 启动 Minecraft dedicated server 是高资源、长时间任务。v1 用 worker
子进程加超时、工作目录隔离和日志截断，能快速实现验证闭环。正式化后可以把验证
迁移到 Docker 沙箱以增强隔离和资源限制。

**备选方案**:

- 不做启动验证：速度快，但服务端生成质量不可控。
- 直接在 API 进程启动验证：会阻塞服务并增加故障影响面。
- 从 v1 开始强制 Docker 沙箱：更安全但实现和调试成本更高。

## 决策：官方服务端检索采用来源适配器模式

**理由**: CurseForge、Modrinth、FTB 的数据结构不同，但 UI 和报告需要统一展示。
使用 `source_clients` 统一输出“官方服务端候选”和“证据记录”，可以让前端、任务
报告和缓存逻辑保持一致。

**备选方案**:

- 在业务逻辑中直接调用各平台：短期快，长期难以维护。
- 只支持一个平台：无法满足宪法中检索范围要求。

## 决策：测试使用 fixture 和缓存响应

**理由**: 外部平台可能限流、不可用或数据变化。功能测试必须能在无网络或弱网络下
稳定运行，因此平台检索和整合包分析都需要 fixture 数据。

**备选方案**:

- 所有测试访问真实平台：不稳定，CI 和本地开发体验差。
- 只写单元测试不做 fixture：无法覆盖真实整合包结构和报告流程。

## 决策：mod 端侧判定采用证据链，而不是单一文件名规则

**理由**: 现有实现只通过文件名命中少量客户端专用规则，容易出现 Xaero's World Map、
Tweakerge、Tweakeroo 等明显客户端工具类 mod 被保留到服务端的情况。服务端生成
必须能解释每个 mod 为什么保留或隔离，因此端侧判定需要按证据强度逐层决策。

**判定优先级**:

1. 平台元数据：优先读取 CurseForge 项目/文件元数据，其次读取 Modrinth 的
   `client_side` / `server_side`；当两者都能提供证据时，CurseForge 优先。
2. jar 内元数据：读取 `fabric.mod.json`、`quilt.mod.json`、`META-INF/mods.toml`
   和 `META-INF/neoforge.mods.toml`，优先使用明确的 `environment`。
3. MCMod 运行环境信息：作为外部参考源，结果必须缓存到本地；来源不可用时不得阻塞生成。
4. 本地维护规则：使用结构化规则兜底，并允许在 `data/rules/` 中积累用户确认的规则。

**失败策略**: 当证据缺失或冲突时，默认 `keep_unknown`，并在报告中标记“不确定”。
只有平台、jar 元数据、MCMod 或本地规则给出明确客户端专用证据时，才隔离到
`_disabled_client_mods/`。

**备选方案**:

- 继续维护纯文件名黑名单：实现最简单，但无法解释证据，也难以处理平台元数据。
- 启动验证失败后再反复试错移除 mod：可能更准，但速度慢、对用户反馈差。
- 完全依赖 MCMod：中文资料有价值，但页面结构和可访问性不稳定，不能作为唯一来源。

## 决策：MCMod provider 作为可缓存参考源，DeepSeek 只做可选歧义辅助

**理由**: `mcmod-classifier` 的实现证明 MCMod “运行环境”字段对中文生态的 mod
端侧判断很有价值。它通过文件名提取搜索关键词，访问 `https://search.mcmod.cn/s`，
进入第一个搜索结果页面后读取运行环境文本，并按 `服务端需装`、`客户端需装`、
`服务端无效`、`客户端无效`、`服务端可选`、`客户端可选` 分类。

本项目不能直接照搬“第一个搜索结果即可信”的策略。MCMod 页面结构、搜索结果质量和
反爬限制都会影响稳定性，因此 provider 必须缓存响应、记录页面 URL 和命中关键词，
并在无法确认唯一候选时返回 `needs_review` 或无证据。

DeepSeek 暂不接入默认判定链。它适合处理候选歧义、中文页面摘要和冲突说明，但不适合
直接决定是否删除/隔离 mod。只有在 MCMod 多候选、页面文本无法规则化解析或证据冲突
需要生成中文解释时，才允许把 DeepSeek 作为可选辅助，并保留原始证据引用。

**备选方案**:

- 完全不用 MCMod：会丢失中文生态里大量有用的“运行环境”人工整理信息。
- 直接把 DeepSeek 作为判定器：实现看似灵活，但不可复现且容易幻觉，不符合证据链原则。
- 照搬 `mcmod-classifier` 单结果分类：速度快，但误匹配风险较高，且缺少缓存和证据报告。

## 决策：增加 Modrinth hash lookup 补足缺失平台标识

**理由**: DeEarthX 的 `HashFilter` 使用 jar 的 SHA1 调用 Modrinth
`POST /v2/version_files`，再按项目 `client_side/server_side` 判断客户端专用 mod。
这能覆盖三类当前容易缺证据的情况：用户上传普通 zip 内直接带 jar、CurseForge
manifest 下载后没有 Modrinth project id、以及文件名被中文启动器重命名的 jar。

本项目将 hash lookup 作为平台证据补充：命中后读取 Modrinth 项目的
`client_side/server_side`，并复用统一合并逻辑。hash 查询结果写入本地缓存，测试使用
fixture，避免依赖实时网络。

**备选方案**:

- 只依赖 `.mrpack` 下载 URL 提取 project id：对非 Modrinth 包和重命名 jar 覆盖不足。
- 只用文件名搜索 Modrinth：易受中文名、版本号和 fork 名称影响，误匹配风险高。
- 每个 jar 单独请求项目：简单但慢；hash 应批量查询并缓存。

## 决策：采用 DeEarthX 的 Modrinth 客户端判断语义，但保留服务端安全覆盖

**理由**: DeEarthX `ModrinthFilter` 将以下情况识别为客户端 mod：

- `client_side=required`
- `client_side=optional` 且 `server_side=unsupported`

这个策略比只判断 `server_side=unsupported` 更激进，能识别更多 UI、渲染、地图和输入类
mod。但本项目目标是“生成可运行服务端”，误删服务端可选或双端 mod 的代价更高，因此
在采用该客户端判断语义的同时，必须额外处理服务端侧：

- `server_side=required` 或 `server_side=optional` 时，优先保留为 `keep_server`。
- 当客户端规则与服务端保留规则冲突时，标记 `needs_review`，默认保留。
- 报告必须说明具体字段值，而不是只显示“Modrinth 判断为客户端”。

**备选方案**:

- 完全照搬 DeEarthX：更容易过滤掉客户端 mod，但可能把 Jade 这类服务端可选 mod 隔离。
- 保持当前保守策略：安全但可能漏掉 `client_side=required` 的客户端强依赖 mod。

## 决策：Mixin 启发式只作为低优先级弱证据

**理由**: DeEarthX `MixinFilter` 的核心规则是：根目录 mixin 配置没有 common
`mixins`，但存在 `client` mixin，且文件名不包含 `lib`，则认为该 jar 倾向客户端专用。
这对渲染、HUD、小地图、键位输入类 mod 很有帮助，也能在平台元数据缺失时提供线索。

但 mixin 结构不是安装端侧声明。部分双端 mod 可能只有客户端 mixin 用于显示增强，同时
服务端仍可安全加载或需要保留。因此本项目将 Mixin 结果作为低置信度证据，只能在没有
平台、jar、MCMod 强证据时推动 `needs_review` 或低置信度 `disable_client_only`，
并允许本地规则或用户确认覆盖。

**备选方案**:

- 不读取 mixin：少一个自动发现客户端工具类 mod 的线索。
- 把 mixin 当强证据：过滤效果更明显，但误伤风险高。

## 决策：本地端侧规则采用“内置规则 + 用户确认规则”双层存储

**理由**: 内置规则覆盖常见客户端专用 mod；用户在实际使用中确认的新规则写入
`data/rules/local_mod_side_rules.json`，不修改随代码发布的规则文件，便于备份、迁移
和后续更新。

**规则格式**:

```json
{
  "match": ["xaerosworldmap", "xaero-world-map"],
  "decision": "disable_client_only",
  "confidence": 0.95,
  "reason": "地图 HUD/全屏地图类客户端功能",
  "source": "builtin_rule"
}
```

**自扩展策略**: v1 不做完全自动学习。系统可以从启动失败日志、用户手动移动记录或
重复出现的未确定结果中生成“候选规则”，但需要用户确认后才写入本地规则，避免误删
服务端必需 mod。
