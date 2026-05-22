# Quickstart：Minecraft 服务端整合包制作应用

## 前置条件

- Docker 和 Docker Compose 可用。
- 本机有足够磁盘空间保存 `data/`。
- 如果需要执行真实启动验证，主机或 worker 镜像需要 Java 17 和 Java 21。
- 如果访问 CurseForge API，需要配置对应 API key；没有 key 时应用必须展示
  “CurseForge 来源暂不可用”或使用 fixture 模式。

## 本地启动

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
pytest
```

前端：

```powershell
cd frontend
npm test
```

## fixture 模式

开发和测试默认允许启用 fixture 模式：

```text
USE_FIXTURES=true
```

fixture 模式下，平台检索使用本地响应样本，整合包分析使用 `backend/tests/fixtures/`
里的小型示例包，避免测试依赖实时网络。

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
