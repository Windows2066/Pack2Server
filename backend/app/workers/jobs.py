from app.services.report_builder import build_failure_report


def run_upload_generate_task(task_id: str) -> str:
    return build_failure_report("生成任务尚未接入完整 worker", [task_id], "请稍后在实现阶段继续完善")


def run_official_search_task(task_id: str) -> str:
    return task_id


def run_cleanup_task() -> str:
    return "清理任务已执行"
