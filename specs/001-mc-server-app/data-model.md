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
