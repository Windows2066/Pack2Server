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

- `source`: `platform_metadata`、`jar_metadata`、`mcmod`、`builtin_rule`、`local_rule`。
- `decision`: `keep_server`、`disable_client_only`、`keep_unknown`、`needs_review`。
- `confidence`: 0 到 1 的置信度。
- `summary`: 中文证据摘要。
- `raw_ref`: 平台项目、jar 内文件路径、MCMod 页面 URL 或规则文件路径。
- `created_at`: 证据创建或读取时间。

合并规则：

- CurseForge 平台元数据优先于 Modrinth 平台元数据；平台元数据整体优先于 jar 元数据。
- jar 元数据优先于 MCMod。
- MCMod 优先于本地规则。
- 证据冲突时保留 mod，决策为 `needs_review` 或 `keep_unknown`，并在报告中列出冲突。

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
