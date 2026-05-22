from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.schemas.task import TaskDetail, TaskStatus, TaskSummary
from app.services.artifact_access import resolve_artifact_path
from app.services.cleanup import is_expired
from app.services.task_repository import get_artifact_path, get_task_detail, list_task_details

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

TASKS: dict[str, TaskDetail] = {}
ARTIFACT_PATHS: dict[str, str] = {}


def _summary_status(task: TaskDetail) -> TaskStatus:
    if task.status == "expired":
        return "expired"
    if task.artifacts and all(is_expired(artifact.expires_at) for artifact in task.artifacts):
        return "expired"
    return task.status


def _summary_message(task: TaskDetail, status: TaskStatus) -> str:
    if status == "expired":
        return "结果已过期，临时文件已清理或不可下载"
    return task.progress_message


@router.get("", response_model=list[TaskSummary])
def list_tasks():
    summaries: list[TaskSummary] = []
    tasks = {task.id: task for task in list_task_details()}
    tasks.update(TASKS)
    for task in tasks.values():
        status = _summary_status(task)
        summaries.append(
            TaskSummary(
                id=task.id,
                type=task.type,
                status=status,
                progress_message=_summary_message(task, status),
                created_at=task.created_at,
            )
        )
    return summaries


@router.get("/{task_id}", response_model=TaskDetail)
def get_task(task_id: str):
    task = get_task_detail(task_id) or TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.get("/{task_id}/events")
def get_task_events(task_id: str):
    task = get_task_detail(task_id) or TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task.events


@router.get("/{task_id}/artifacts/{artifact_id}/download")
def download_artifact(task_id: str, artifact_id: str):
    task = get_task_detail(task_id) or TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="产物不存在或已过期")

    artifact = next((item for item in task.artifacts if item.id == artifact_id), None)
    if not artifact or is_expired(artifact.expires_at):
        raise HTTPException(status_code=404, detail="产物不存在或已过期")

    relative_path = get_artifact_path(task_id, artifact_id) or ARTIFACT_PATHS.get(f"{task_id}:{artifact_id}")
    if not relative_path:
        raise HTTPException(status_code=404, detail="产物不存在或已过期")

    try:
        artifact_path = resolve_artifact_path(relative_path)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="产物不存在或已过期") from exc

    if not artifact_path.is_file():
        raise HTTPException(status_code=404, detail="产物不存在或已过期")

    return FileResponse(
        artifact_path,
        media_type="application/zip",
        filename=artifact.download_name,
    )
