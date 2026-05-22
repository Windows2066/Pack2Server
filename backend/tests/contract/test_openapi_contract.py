from fastapi.testclient import TestClient

from app.main import app


def test_core_routes_are_registered():
    client = TestClient(app)
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]

    assert "/health" in paths
    assert "/api/tasks" in paths
    assert "/api/uploads" in paths
    assert "/api/search/official-server" in paths
    assert "/api/tasks/{task_id}" in paths
