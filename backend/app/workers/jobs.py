import asyncio
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from app.api.routes_tasks import TASKS
from app.schemas.task import TaskDetail, TaskEventRead
from app.services.archive_analyzer import analyze_archive
from app.services.mod_decider import decide_mod_side
from app.services.query_parser import parse_pack_query
from app.services.official_server_search import search_official_servers
from app.services.report_builder import build_failure_report, build_success_report


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
        _add_event(task, task.stage, "开始分析整合包 manifest")

        if not task.input_summary:
            raise ValueError("任务缺少上传文件路径")

        analysis = analyze_archive(Path(task.input_summary))
        decisions = [decide_mod_side(mod_file) for mod_file in analysis.mod_files]
        disabled_mods = sum(1 for decision, _, _ in decisions if decision == "disable_client_only")
        kept_mods = len(decisions) - disabled_mods

        report = build_success_report(
            pack_name=analysis.pack_name or "未识别整合包",
            minecraft_version=analysis.minecraft_version,
            loader=analysis.loader,
            kept_mods=kept_mods,
            disabled_mods=disabled_mods,
        )
        task.status = "succeeded"
        task.stage = "completed"
        task.progress_message = "服务端生成任务已完成基础分析"
        task.pack_identity = {
            "pack_name": analysis.pack_name,
            "pack_version": analysis.pack_version,
            "minecraft_version": analysis.minecraft_version,
            "loader": analysis.loader,
        }
        task.report = report
        _add_event(task, task.stage, "已生成基础分析报告")
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
