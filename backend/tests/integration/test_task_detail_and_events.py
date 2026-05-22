from fastapi.testclient import TestClient

from app.main import app


def test_task_not_found_returns_404_message():
    client = TestClient(app)

    response = client.get("/api/tasks/not-exist")

    assert response.status_code == 404
    assert "任务不存在" in response.json()["detail"]


def test_task_events_not_found_returns_404_message():
    client = TestClient(app)

    response = client.get("/api/tasks/not-exist/events")

    assert response.status_code == 404
    assert "任务不存在" in response.json()["detail"]
