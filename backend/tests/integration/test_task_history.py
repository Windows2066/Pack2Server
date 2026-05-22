from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.api.routes_tasks import TASKS
from app.main import app
from app.schemas.task import ArtifactRead, TaskDetail


def test_recent_tasks_returns_list():
    client = TestClient(app)

    response = client.get("/api/tasks")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_recent_tasks_marks_expired_artifacts_as_expired():
    task_id = "expired-task"
    now = datetime.now(UTC)
    TASKS[task_id] = TaskDetail(
        id=task_id,
        type="upload_generate",
        status="succeeded",
        stage="completed",
        progress_message="服务端生成完成",
        created_at=now,
        artifacts=[
            ArtifactRead(
                id="server-zip",
                kind="server_archive",
                download_name="server.zip",
                expires_at=now - timedelta(seconds=1),
            )
        ],
    )
    client = TestClient(app)

    try:
        response = client.get("/api/tasks")
    finally:
        TASKS.pop(task_id, None)

    assert response.status_code == 200
    task = next(item for item in response.json() if item["id"] == task_id)
    assert task["status"] == "expired"
    assert "已过期" in task["progress_message"]
