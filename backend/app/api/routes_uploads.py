from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile

from app.core.config import get_settings
from app.schemas.task import TaskCreated, TaskDetail
from app.services.upload_storage import save_upload
from app.api.routes_tasks import TASKS
from app.workers.jobs import run_upload_generate_task
from app.workers.queue import enqueue_or_run_job

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("", response_model=TaskCreated, status_code=202)
async def upload_pack(file: UploadFile):
    try:
        _, path, size = await save_upload(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    task_id = uuid4().hex
    now = datetime.now(UTC)
    TASKS[task_id] = TaskDetail(
        id=task_id,
        type="upload_generate",
        status="queued",
        stage="upload_validation",
        progress_message="生成任务已创建，等待分析整合包",
        input_summary=str(path),
        created_at=now,
        events=[],
        artifacts=[],
    )
    enqueue_or_run_job(run_upload_generate_task, task_id)
    return TaskCreated(task_id=task_id, message="生成任务已创建")
