from fastapi.testclient import TestClient

from app.main import app


def test_recent_tasks_returns_list():
    client = TestClient(app)

    response = client.get("/api/tasks")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
