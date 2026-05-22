from datetime import datetime
from typing import Literal

from pydantic import BaseModel


TaskStatus = Literal["queued", "running", "waiting_user_choice", "succeeded", "failed", "expired"]
TaskType = Literal["upload_generate", "official_search"]


class TaskCreated(BaseModel):
    task_id: str
    status: Literal["queued"] = "queued"
    message: str


class TaskEventRead(BaseModel):
    stage: str
    level: str
    message: str
    created_at: datetime


class ArtifactRead(BaseModel):
    id: str
    kind: str
    download_name: str
    expires_at: datetime | None = None


class TaskSummary(BaseModel):
    id: str
    type: TaskType
    status: TaskStatus
    progress_message: str
    created_at: datetime


class TaskDetail(TaskSummary):
    stage: str
    events: list[TaskEventRead] = []
    artifacts: list[ArtifactRead] = []
    error_message: str | None = None
    pack_identity: dict | None = None
    official_candidates: list[dict] = []
