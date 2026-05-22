# Quickstart：Minecraft 服务端整合包制作应用

## 前置条件

- Python 3.12 可用。
- Node.js 20 或兼容版本可用。
- 本机有足够磁盘空间保存 `data/`。
- 如果需要执行真实启动验证，本机需要 Java 17 或 Java 21。
- 如果访问 CurseForge API，需要配置对应 API key；没有 key 时应用必须展示
  “CurseForge 来源暂不可用”或使用 fixture 模式。

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

启动后访问：

```text
http://localhost:5173
```

后端 API：

```text
http://localhost:8000
```

## 上传生成服务端流程

1. 打开首页。
2. 选择“上传整合包生成服务端”。
3. 上传 `.zip` 或 `.mrpack`。
4. 查看文件名、大小和基础校验结果。
5. 提交任务。
6. 在任务页查看“上传校验、整合包分析、服务端生成、启动验证”进度。
7. 完成后下载服务端产物，或查看失败报告。

## 自然语言查找官方服务端流程

1. 打开首页。
2. 选择“自然语言查找官方服务端”。
3. 输入类似“我想要 ATM10 最新版服务端”。
4. 应用展示候选整合包；如果只有一个高置信候选则直接检索。
5. 如果找到官方服务端，页面展示来源、版本和获取方式。
6. 如果未找到，页面必须明确展示“未找到官方服务端”，并列出已检索的
   CurseForge、Modrinth、FTB。

## 测试

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

## fixture 模式

开发和测试默认允许启用 fixture 模式：

```text
USE_FIXTURES=true
```

fixture 模式下，平台检索使用本地响应样本，整合包分析使用 `backend/tests/fixtures/`
里的小型示例包，避免测试依赖实时网络。

如需执行真实官方服务端检索：

```text
USE_FIXTURES=false
CURSEFORGE_API_KEY=<你的 CurseForge API key>
```

Modrinth 可直接使用公开 API；CurseForge 没有 API key 时会跳过；FTB 会从官方
Server Files 页面提取服务端安装器链接，无法确认匹配时返回空结果。

## 数据目录

```text
data/
├── uploads/      # 原始上传
├── workspaces/   # 解压和处理工作区
├── artifacts/    # 服务端产物
├── reports/      # 中文报告和日志摘录
└── cache/        # 平台响应和端侧规则缓存
```

## 清理策略

默认保留任务产物 72 小时。清理任务必须删除过期上传、工作区和产物，但保留必要的
结构化任务摘要和可复用知识。

## 二期部署说明

Docker Compose、服务器镜像拉取、Redis 独立 worker 和云服务器长期运行配置放到二期。
当前一期只要求本地前端、后端、测试和构建正常运行。
