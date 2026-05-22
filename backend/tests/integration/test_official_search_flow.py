from fastapi.testclient import TestClient

from app.main import app


def test_official_search_returns_task_with_chinese_message():
    client = TestClient(app)

    response = client.post("/api/search/official-server", json={"query": "ATM10 最新版"})

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert "检索任务已创建" in body["message"]


def test_empty_official_search_rejected():
    client = TestClient(app)

    response = client.post("/api/search/official-server", json={"query": ""})

    assert response.status_code == 400
    assert "请输入" in response.json()["detail"]
