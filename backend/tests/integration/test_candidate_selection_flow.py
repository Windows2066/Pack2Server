from fastapi.testclient import TestClient

from app.api import routes_search
from app.main import app
from app.services.deepseek_query_parser import QueryCandidate


async def _fake_candidates(_query: str, api_key: str | None = None):
    return [
        QueryCandidate(
            query="ATM10",
            version_hint="latest",
            source_hint=None,
            confidence=0.86,
            reason="用户提到 ATM10 最新版",
        ),
        QueryCandidate(
            query="All the Mods 9",
            version_hint=None,
            source_hint="curseforge",
            confidence=0.52,
            reason="相近名称候选",
        ),
    ]


def test_official_search_waits_for_user_choice_when_deepseek_returns_candidates(monkeypatch):
    monkeypatch.setattr(routes_search, "parse_query_candidates", _fake_candidates)
    client = TestClient(app)

    response = client.post("/api/search/official-server", json={"query": "帮我找 ATM 服务端"})

    assert response.status_code == 202
    task_id = response.json()["task_id"]
    detail = client.get(f"/api/tasks/{task_id}")
    assert detail.status_code == 200
    detail_body = detail.json()
    assert detail_body["status"] == "waiting_user_choice"
    assert detail_body["stage"] == "candidate_selection"
    assert len(detail_body["official_candidates"]) == 2

    selected = client.post(f"/api/search/official-server/{task_id}/candidates/0")
    assert selected.status_code == 202
    selected_detail = client.get(f"/api/tasks/{task_id}").json()
    assert selected_detail["status"] == "succeeded"
    assert "已检索来源" in selected_detail["report"]
