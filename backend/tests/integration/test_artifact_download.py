from fastapi.testclient import TestClient

from app.main import app


def test_missing_artifact_returns_404_message():
    client = TestClient(app)

    response = client.get("/api/tasks/not-exist/artifacts/nope/download")

    assert response.status_code == 404
    assert "产物不存在或已过期" in response.json()["detail"]
