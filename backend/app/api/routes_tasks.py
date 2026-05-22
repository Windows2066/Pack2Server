from fastapi import APIRouter, HTTPException

from app.schemas.task import TaskDetail, TaskStatus, TaskSummary
from app.services.cleanup import is_expired

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

TASKS: dict[str, TaskDetail] = {}


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
    for task in TASKS.values():
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
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.get("/{task_id}/events")
def get_task_events(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task.events


@router.get("/{task_id}/artifacts/{artifact_id}/download")
def download_artifact(task_id: str, artifact_id: str):
    raise HTTPException(status_code=404, detail="产物不存在或已过期")
