import json
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.models import Artifact, Task, TaskEvent
from app.db.session import SessionLocal
from app.schemas.task import ArtifactRead, TaskDetail, TaskEventRead


def save_task_detail(task: TaskDetail, artifact_paths: dict[str, str] | None = None) -> None:
    with SessionLocal() as db:
        _save_task_detail(db, task, artifact_paths or {})
        db.commit()


def get_task_detail(task_id: str) -> TaskDetail | None:
    with SessionLocal() as db:
        task = db.get(Task, task_id)
        if task is None:
            return None
        return _to_detail(task)


def list_task_details() -> list[TaskDetail]:
    with SessionLocal() as db:
        tasks = db.query(Task).order_by(Task.created_at.desc()).all()
        return [_to_detail(task) for task in tasks]


def get_artifact_path(task_id: str, artifact_id: str) -> str | None:
    with SessionLocal() as db:
        artifact = db.get(Artifact, artifact_id)
        if artifact is None or artifact.task_id != task_id:
            return None
        return artifact.path


def _save_task_detail(db: Session, detail: TaskDetail, artifact_paths: dict[str, str]) -> None:
    task = db.get(Task, detail.id)
    if task is None:
        task = Task(id=detail.id, type=detail.type)
        db.add(task)

    task.type = detail.type
    task.status = detail.status
    task.stage = detail.stage
    task.progress_message = detail.progress_message
    task.input_summary = detail.input_summary
    task.error_message = detail.error_message
    task.pack_identity_json = _dump_json(detail.pack_identity)
    task.official_candidates_json = _dump_json(detail.official_candidates)
    task.report = detail.report
    task.created_at = detail.created_at
    task.updated_at = datetime.now(UTC)

    existing_artifact_paths = {
        artifact.id: artifact.path
        for artifact in db.query(Artifact).filter(Artifact.task_id == detail.id).all()
    }
    db.query(TaskEvent).filter(TaskEvent.task_id == detail.id).delete()
    db.query(Artifact).filter(Artifact.task_id == detail.id).delete()
    db.flush()

    for event in detail.events:
        db.add(
            TaskEvent(
                task_id=detail.id,
                stage=event.stage,
                level=event.level,
                message=event.message,
                created_at=event.created_at,
            )
        )

    for artifact in detail.artifacts:
        path = artifact_paths.get(artifact.id) or existing_artifact_paths.get(artifact.id) or artifact.download_name
        db.add(
            Artifact(
                id=artifact.id,
                task_id=detail.id,
                kind=artifact.kind,
                path=path,
                size_bytes=0,
                download_name=artifact.download_name,
                expires_at=artifact.expires_at,
            )
        )


def _to_detail(task: Task) -> TaskDetail:
    return TaskDetail(
        id=task.id,
        type=task.type,
        status=task.status,
        stage=task.stage,
        progress_message=task.progress_message,
        input_summary=task.input_summary,
        created_at=task.created_at,
        events=[
            TaskEventRead(
                stage=event.stage,
                level=event.level,
                message=event.message,
                created_at=event.created_at,
            )
            for event in sorted(task.events, key=lambda item: item.created_at)
        ],
        artifacts=[
            ArtifactRead(
                id=artifact.id,
                kind=artifact.kind,
                download_name=artifact.download_name,
                expires_at=artifact.expires_at,
            )
            for artifact in task.artifacts
        ],
        error_message=task.error_message,
        pack_identity=_load_json_object(task.pack_identity_json),
        official_candidates=_load_json_list(task.official_candidates_json),
        report=task.report,
    )


def _dump_json(value: object) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def _load_json_object(value: str | None) -> dict | None:
    if not value:
        return None
    loaded = json.loads(value)
    return loaded if isinstance(loaded, dict) else None


def _load_json_list(value: str | None) -> list[dict]:
    if not value:
        return []
    loaded = json.loads(value)
    return loaded if isinstance(loaded, list) else []
