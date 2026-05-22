from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.routes_tasks import TASKS
from app.schemas.task import TaskCreated, TaskDetail
from app.services.query_parser import parse_pack_query
from app.workers.jobs import run_official_search_task
from app.workers.queue import enqueue_or_run_job

router = APIRouter(prefix="/api/search", tags=["search"])


class OfficialSearchRequest(BaseModel):
    query: str


@router.post("/official-server", response_model=TaskCreated, status_code=202)
def create_official_search(request: OfficialSearchRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="请输入要查找的整合包名称或描述")

    parsed = parse_pack_query(request.query)
    task_id = uuid4().hex
    now = datetime.now(UTC)
    TASKS[task_id] = TaskDetail(
        id=task_id,
        type="official_search",
        status="queued",
        stage="source_lookup",
        progress_message="检索任务已创建，等待查询官方服务端",
        input_summary=parsed.query,
        created_at=now,
        events=[],
        artifacts=[],
    )
    enqueue_or_run_job(run_official_search_task, task_id)
    return TaskCreated(task_id=task_id, message="检索任务已创建")
