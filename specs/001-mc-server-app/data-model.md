# 数据模型：Minecraft 服务端整合包制作应用

## 用户任务 Task

表示一次上传生成或自然语言检索请求。

字段：

- `id`: 任务唯一标识。
- `type`: `upload_generate` 或 `official_search`。
- `status`: `queued`、`running`、`waiting_user_choice`、`succeeded`、`failed`、`expired`。
- `stage`: 当前阶段，包含 `upload_validation`、`source_lookup`、`pack_analysis`、
  `server_generation`、`startup_verification`、`completed`。
- `progress_message`: 中文进度说明。
- `input_summary`: 用户输入摘要，不保存不必要的敏感信息。
- `created_at`: 创建时间。
- `updated_at`: 更新时间。
- `expires_at`: 结果过期时间。
- `error_code`: 失败代码。
- `error_message`: 中文失败说明。

状态转换：

```text
queued -> running -> succeeded
queued -> running -> failed
running -> waiting_user_choice -> running
succeeded -> expired
failed -> expired
```

## 上传文件 Upload

表示用户上传的整合包压缩包。

字段：

- `id`: 上传记录唯一标识。
- `task_id`: 所属任务。
- `original_filename`: 原始文件名。
- `content_type`: 上传内容类型。
- `size_bytes`: 文件大小。
- `sha256`: 文件哈希。
- `stored_path`: 本地保存路径。
- `validation_status`: `valid`、`invalid`、`unsupported`。
- `validation_message`: 中文校验说明。

验证规则：

- 文件必须在配置的最大体积限制内。
- 文件必须是支持的压缩包格式。
- 压缩包不得包含路径穿越条目。

## 整合包识别结果 PackIdentity

表示从上传文件或自然语言中识别出的整合包信息。

字段：

- `id`: 识别结果唯一标识。
- `task_id`: 所属任务。
- `source`: `curseforge`、`modrinth`、`ftb`、`local`、`unknown`。
- `pack_name`: 整合包名称。
- `pack_slug`: 平台 slug 或规范化名称。
- `pack_version`: 整合包版本。
- `minecraft_version`: Minecraft 版本。
- `loader`: `forge`、`neoforge`、`fabric`、`quilt`、`unknown`。
- `confidence`: 0 到 1 的置信度。
- `uncertain_fields`: 无法确定或冲突的字段列表。

## 官方服务端候选 OfficialServerCandidate

表示从平台检索到的官方服务端结果。

字段：

- `id`: 候选唯一标识。
- `task_id`: 所属任务。
- `source`: 来源平台。
- `pack_name`: 匹配整合包名称。
- `pack_version`: 匹配版本。
- `minecraft_version`: Minecraft 版本。
- `loader`: loader 类型。
- `download_url`: 下载地址或获取方式。
- `published_at`: 发布时间。
- `match_reason`: 中文匹配原因。
- `confidence`: 0 到 1 的置信度。

## mod 决策记录 ModDecision

表示对单个 mod 是否放入服务端的判断。

字段：

- `id`: 决策唯一标识。
- `task_id`: 所属任务。
- `mod_id`: mod id。
- `filename`: jar 文件名。
- `version`: mod 版本。
- `decision`: `keep_server`、`disable_client_only`、`keep_unknown`、`needs_review`。
- `confidence`: 0 到 1 的置信度。
- `reason`: 中文说明。
- `evidence_ids`: 关联证据。
- `evidence_source`: 当前主导决策的证据来源，包含 `platform_metadata`、`jar_metadata`、
  `mcmod`、`builtin_rule`、`local_rule`、`unknown`。
- `matched_rule`: 命中的本地规则标识，未命中时为空。

## mod 端侧证据 ModSideEvidence

表示某个来源对 mod 安装端侧的判断。

字段：

- `source`: `curseforge_metadata`、`modrinth_metadata`、`modrinth_hash`、`jar_metadata`、
  `mcmod`、`mixin_heuristic`、`builtin_rule`、`local_rule`、`deepseek_assist`。
- `decision`: `keep_server`、`disable_client_only`、`keep_unknown`、`needs_review`。
- `confidence`: 0 到 1 的置信度。
- `summary`: 中文证据摘要。
- `raw_ref`: 平台项目、jar 内文件路径、MCMod 页面 URL 或规则文件路径。
- `raw_fields`: 原始关键字段快照，例如 Modrinth `client_side/server_side`、MCMod
  `服务端需装/服务端无效`、mixin 配置中的 `client/mixins/server` 数量。
- `cache_key`: 来源缓存键；没有缓存时为空。
- `created_at`: 证据创建或读取时间。

合并规则：

- CurseForge 平台元数据优先于 Modrinth 平台元数据；平台元数据整体优先于 jar 元数据。
- Modrinth manifest/project id 证据优先于 Modrinth hash lookup；hash lookup 只补足缺失平台标识。
- jar 元数据优先于 MCMod。
- MCMod 优先于 Mixin 启发式和本地规则。
- Mixin 启发式为低优先级弱证据，不得覆盖明确服务端可用证据。
- DeepSeek 只允许作为 `needs_review` 解释或候选规则建议，不得直接产生强制隔离结论。
- 证据冲突时保留 mod，决策为 `needs_review` 或 `keep_unknown`，并在报告中列出冲突。

## MCMod 缓存记录 MCModCacheEntry

表示从 MCMod 检索和解析出的运行环境参考信息。

字段：

- `cache_key`: 由规范化查询词、mod id 或文件名生成的缓存键。
- `query`: 实际搜索关键词。
- `matched_url`: 命中的 MCMod 模组页 URL。
- `matched_title`: 命中的模组标题。
- `run_environment_text`: 原始运行环境文本。
- `client_requirement`: `required`、`optional`、`unsupported`、`unknown`。
- `server_requirement`: `required`、`optional`、`unsupported`、`unknown`。
- `confidence`: 候选匹配和字段解析综合置信度。
- `fetched_at`: 抓取时间。
- `expires_at`: 缓存过期时间。
- `error`: 检索失败、页面不可解析或未收录时的中文说明。

验证规则：

- MCMod 页面不可用、限流或未收录时，必须返回无证据并记录可读原因，不得中断生成。
- 搜索结果存在多个候选且无法唯一确认时，必须返回 `needs_review` 或无证据。
- MCMod 证据必须在报告中展示页面 URL、运行环境原文摘要和缓存时间。

## Modrinth hash lookup 记录 ModrinthHashLookup

表示通过 jar SHA1 反查 Modrinth 项目的缓存结果。

字段：

- `sha1`: jar 文件 SHA1。
- `filename`: 查询时的 jar 文件名。
- `project_id`: Modrinth 项目 id。
- `version_id`: Modrinth 文件版本 id。
- `client_side`: Modrinth 项目端侧字段。
- `server_side`: Modrinth 项目端侧字段。
- `queried_at`: 查询时间。
- `expires_at`: 缓存过期时间。
- `error`: 未命中或请求失败时的中文说明。

验证规则：

- hash lookup 必须批量查询并缓存，避免对每个 jar 单独请求。
- hash 未命中不能降低原有证据置信度，只能作为“未获得平台证据”记录。
- 查询结果必须通过统一端侧合并逻辑产生 `ModSideEvidence`。

## Mixin 启发式记录 MixinHeuristicEvidence

表示从 jar 根目录 mixin 配置推断出的弱端侧线索。

字段：

- `filename`: jar 文件名。
- `mixin_files`: 参与判断的根目录 `*.mixins.json` 文件名。
- `client_entries`: `client` mixin 条目数量。
- `common_entries`: `mixins` 条目数量。
- `server_entries`: `server` 条目数量。
- `decision`: `needs_review` 或低置信度 `disable_client_only`。
- `reason`: 中文说明。

验证规则：

- 只有存在 `client` 条目、没有 common `mixins` 条目，且文件名不明显为库文件时，才能生成客户端倾向证据。
- 该证据不得覆盖平台、jar 元数据或 MCMod 的明确服务端可用结论。

## 本地端侧规则 LocalModSideRule

表示用户确认或系统内置的端侧兜底规则。

字段：

- `match`: 文件名、mod id 或 slug 片段列表。
- `decision`: `disable_client_only`、`keep_server` 或 `needs_review`。
- `confidence`: 规则置信度。
- `reason`: 中文原因。
- `source`: `builtin_rule` 或 `local_rule`。
- `created_at`: 本地规则创建时间，内置规则可为空。
- `hit_count`: 命中次数，用于后续清理和排序。
- `last_confirmed_at`: 用户最后确认时间，内置规则可为空。

验证规则：

- 本地规则不得直接覆盖更高优先级的明确平台元数据。
- 自动生成的候选规则必须由用户确认后才能写入 `data/rules/local_mod_side_rules.json`。
- 规则文件损坏时必须忽略本地规则并返回中文警告，不得中断服务端生成。

## 证据记录 EvidenceRecord

表示用于支撑检索、分析、生成和验证结论的证据。

字段：

- `id`: 证据唯一标识。
- `task_id`: 所属任务。
- `kind`: `platform_metadata`、`manifest`、`jar_metadata`、`rule`、`runtime_log`、
  `cache`、`user_input`。
- `source`: 证据来源。
- `summary`: 中文摘要。
- `raw_ref`: 原始文件、URL、缓存键或日志位置。
- `created_at`: 记录时间。

## 生成产物 Artifact

表示可下载或可查看的结果。

字段：

- `id`: 产物唯一标识。
- `task_id`: 所属任务。
- `kind`: `server_archive`、`report`、`log_excerpt`、`disabled_mods_manifest`。
- `path`: 本地路径。
- `size_bytes`: 文件大小。
- `download_name`: 下载文件名。
- `expires_at`: 过期时间。

## 任务事件 TaskEvent

表示任务进度流水。

字段：

- `id`: 事件唯一标识。
- `task_id`: 所属任务。
- `stage`: 阶段。
- `level`: `info`、`warning`、`error`。
- `message`: 中文消息。
- `created_at`: 事件时间。
