from fastapi import APIRouter, HTTPException

from app.schemas.task import TaskDetail, TaskSummary

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

TASKS: dict[str, TaskDetail] = {}


@router.get("", response_model=list[TaskSummary])
def list_tasks():
    return [
        TaskSummary(
            id=task.id,
            type=task.type,
            status=task.status,
            progress_message=task.progress_message,
            created_at=task.created_at,
        )
        for task in TASKS.values()
    ]


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
