from fastapi.testclient import TestClient

from app.main import app
from app.services.official_server_search import clear_official_server_cache


def test_official_search_returns_task_with_chinese_message():
    clear_official_server_cache()
    client = TestClient(app)

    response = client.post("/api/search/official-server", json={"query": "ATM10 最新版"})

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert "检索任务已创建" in body["message"]

    detail = client.get(f"/api/tasks/{body['task_id']}")
    assert detail.status_code == 200
    detail_body = detail.json()
    assert detail_body["status"] == "succeeded"
    assert detail_body["official_candidates"]
    assert "已检索来源" in detail_body["report"]


def test_empty_official_search_rejected():
    client = TestClient(app)

    response = client.post("/api/search/official-server", json={"query": ""})

    assert response.status_code == 400
    assert "请输入" in response.json()["detail"]
