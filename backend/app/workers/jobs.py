import asyncio
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.api.routes_tasks import ARTIFACT_PATHS, TASKS
from app.core.config import get_settings
from app.core.paths import data_root
from app.schemas.task import ArtifactRead, TaskDetail, TaskEventRead
from app.services.archive_analyzer import analyze_archive
from app.services.query_parser import parse_pack_query
from app.services.official_server_search import search_official_servers
from app.services.report_builder import build_failure_report, build_success_report
from app.services.server_generator import build_runnable_server_artifact


def _add_event(task: TaskDetail, stage: str, message: str, level: str = "info") -> None:
    task.events.append(
        TaskEventRead(stage=stage, level=level, message=message, created_at=datetime.now(UTC))
    )


def run_upload_generate_task(task_id: str) -> str:
    task = TASKS.get(task_id)
    if task is None:
        return build_failure_report("生成任务不存在", [task_id], "请重新上传整合包")

    try:
        task.status = "running"
        task.stage = "pack_analysis"
        task.progress_message = "正在分析整合包"
        _add_event(task, task.stage, "开始分析整合包清单文件")

        if not task.input_summary:
            raise ValueError("任务缺少上传文件路径")

        analysis = analyze_archive(Path(task.input_summary))
        task.stage = "server_generation"
        task.progress_message = "正在生成本地服务端目录"
        _add_event(task, task.stage, "开始复制服务端文件并隔离客户端专用 mod")

        generated = build_runnable_server_artifact(
            task_id=task_id,
            upload_archive=Path(task.input_summary),
            workspace_root=data_root() / "workspaces",
            artifact_root=data_root() / "artifacts",
            analysis=analysis,
        )
        artifact_id = "server-archive"
        artifact_name = f"{task_id}-server.zip"
        artifact_relative_path = generated.archive_path.resolve().relative_to(
            (data_root() / "artifacts").resolve()
        )
        ARTIFACT_PATHS[f"{task_id}:{artifact_id}"] = artifact_relative_path.as_posix()

        report = build_success_report(
            pack_name=analysis.pack_name or "未识别整合包",
            minecraft_version=analysis.minecraft_version,
            loader=analysis.loader,
            kept_mods=generated.kept_mods,
            disabled_mods=generated.disabled_mods,
        )
        task.status = "succeeded"
        task.stage = "completed"
        task.progress_message = "服务端生成完成，可以下载产物"
        task.pack_identity = {
            "pack_name": analysis.pack_name,
            "pack_version": analysis.pack_version,
            "minecraft_version": analysis.minecraft_version,
            "loader": analysis.loader,
        }
        task.artifacts = [
            ArtifactRead(
                id=artifact_id,
                kind="server_archive",
                download_name=artifact_name,
                expires_at=datetime.now(UTC)
                + timedelta(hours=get_settings().artifact_retention_hours),
            )
        ]
        task.report = report
        _add_event(task, task.stage, "已生成可下载服务端压缩包")
        return report
    except Exception as exc:
        task.status = "failed"
        task.progress_message = "服务端生成失败"
        task.error_message = str(exc)
        task.report = build_failure_report("服务端生成失败", [str(exc)], "请检查整合包格式后重试")
        _add_event(task, task.stage, f"生成失败：{exc}", "error")
        return task.report


def run_official_search_task(task_id: str) -> str:
    task = TASKS.get(task_id)
    if task is None:
        return task_id

    task.status = "running"
    task.stage = "source_lookup"
    task.progress_message = "正在检索官方服务端"
    _add_event(task, task.stage, "开始检索 CurseForge、Modrinth 和 FTB")

    parsed = parse_pack_query(task.input_summary or "")
    results, searched = asyncio.run(search_official_servers(parsed))
    task.official_candidates = [asdict(result) for result in results]
    task.status = "succeeded"
    task.stage = "completed"
    if results:
        task.progress_message = "已找到可能的官方服务端结果"
        task.report = f"已检索来源：{', '.join(searched)}；找到 {len(results)} 个候选结果。"
    else:
        task.progress_message = "未找到官方服务端"
        task.report = f"已检索来源：{', '.join(searched)}；未找到官方服务端。"
    _add_event(task, task.stage, task.progress_message)
    return task_id


def run_cleanup_task() -> str:
    return "清理任务已执行"
