import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.routes_tasks import TASKS
from app.schemas.task import TaskCreated, TaskDetail
from app.services.deepseek_query_parser import parse_query_candidates
from app.services.task_repository import get_task_detail, save_task_detail
from app.workers.jobs import run_official_search_task
from app.workers.queue import enqueue_or_run_job

router = APIRouter(prefix="/api/search", tags=["search"])


class OfficialSearchRequest(BaseModel):
    query: str


@router.post("/official-server", response_model=TaskCreated, status_code=202)
def create_official_search(request: OfficialSearchRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="请输入要查找的整合包名称或描述")

    candidates = asyncio.run(parse_query_candidates(request.query))
    task_id = uuid4().hex
    now = datetime.now(UTC)
    task = TaskDetail(
        id=task_id,
        type="official_search",
        status="waiting_user_choice" if len(candidates) > 1 else "queued",
        stage="candidate_selection" if len(candidates) > 1 else "source_lookup",
        progress_message="请选择要检索的候选整合包" if len(candidates) > 1 else "检索任务已创建，等待查询官方服务端",
        input_summary=candidates[0].query if candidates else request.query.strip(),
        created_at=now,
        events=[],
        artifacts=[],
        official_candidates=[candidate.model_dump() for candidate in candidates],
        pack_identity={
            "version_hint": candidates[0].version_hint,
            "source_hint": candidates[0].source_hint,
        }
        if candidates
        else None,
        report="DeepSeek 返回多个可能候选，请选择一个后继续检索。" if len(candidates) > 1 else None,
    )
    TASKS[task_id] = task
    save_task_detail(task)
    if len(candidates) <= 1:
        enqueue_or_run_job(run_official_search_task, task_id)
    return TaskCreated(task_id=task_id, message="检索任务已创建")


@router.post("/official-server/{task_id}/candidates/{candidate_index}", response_model=TaskCreated, status_code=202)
def select_official_search_candidate(task_id: str, candidate_index: int):
    task = get_task_detail(task_id) or TASKS.get(task_id)
    if task is None or task.type != "official_search":
        raise HTTPException(status_code=404, detail="任务不存在")
    if candidate_index < 0 or candidate_index >= len(task.official_candidates):
        raise HTTPException(status_code=400, detail="候选项不存在")

    candidate = task.official_candidates[candidate_index]
    task.input_summary = str(candidate.get("query") or task.input_summary or "")
    task.pack_identity = {
        "version_hint": candidate.get("version_hint"),
        "source_hint": candidate.get("source_hint"),
        "selected_candidate": candidate,
    }
    task.status = "queued"
    task.stage = "source_lookup"
    task.progress_message = "已选择候选整合包，等待查询官方服务端"
    task.report = None
    TASKS[task_id] = task
    save_task_detail(task)
    enqueue_or_run_job(run_official_search_task, task_id)
    return TaskCreated(task_id=task_id, message="已选择候选整合包，检索任务已创建")
