import pytest
from httpx import AsyncClient, MockTransport, Request, Response

from app.services.deepseek_query_parser import parse_query_candidates


@pytest.mark.asyncio
async def test_parse_query_candidates_uses_deepseek_json_response():
    def handler(request: Request) -> Response:
        assert request.headers["Authorization"] == "Bearer test-key"
        return Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"candidates":[{"query":"ATM10","version_hint":"latest",'
                                '"source_hint":null,"confidence":0.91,"reason":"用户提到 ATM10 最新版"},'
                                '{"query":"All the Mods 9","version_hint":null,'
                                '"source_hint":"curseforge","confidence":0.55,"reason":"可能的相近整合包"}]}'
                            )
                        }
                    }
                ]
            },
        )

    async with AsyncClient(transport=MockTransport(handler), base_url="https://api.deepseek.com") as client:
        candidates = await parse_query_candidates(
            "我想要 ATM10 最新版服务端",
            api_key="test-key",
            client=client,
        )

    assert candidates[0].query == "ATM10"
    assert candidates[0].version_hint == "latest"
    assert candidates[0].confidence == 0.91
    assert candidates[1].source_hint == "curseforge"


@pytest.mark.asyncio
async def test_parse_query_candidates_falls_back_without_api_key():
    candidates = await parse_query_candidates("我想要 ATM10 最新版服务端", api_key=None)

    assert len(candidates) == 1
    assert candidates[0].query == "ATM10"
    assert candidates[0].version_hint == "latest"
