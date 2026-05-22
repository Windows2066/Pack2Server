from datetime import UTC, datetime

from app.db.models import TaskEvent


def add_event(db, task_id: str, stage: str, message: str, level: str = "info") -> TaskEvent:
    event = TaskEvent(
        task_id=task_id,
        stage=stage,
        level=level,
        message=message,
        created_at=datetime.now(UTC),
    )
    db.add(event)
    return event
