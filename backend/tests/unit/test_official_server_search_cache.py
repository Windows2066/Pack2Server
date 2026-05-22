import pytest

from app.services import official_server_search
from app.services.query_parser import ParsedQuery
from app.sources.models import SourceSearchResult


@pytest.mark.asyncio
async def test_official_search_reuses_cached_results(monkeypatch):
    official_server_search.clear_official_server_cache()
    calls = {"modrinth": 0, "curseforge": 0, "ftb": 0}

    async def fake_modrinth(query: str):
        calls["modrinth"] += 1
        return [
            SourceSearchResult(
                source="modrinth",
                pack_name=query,
                pack_version="latest",
                minecraft_version=None,
                loader=None,
                download_url=None,
                match_reason="缓存测试",
                confidence=0.9,
            )
        ]

    async def fake_empty(source: str):
        async def _inner(query: str):
            calls[source] += 1
            return []

        return _inner

    monkeypatch.setattr(official_server_search, "search_modrinth_official_server", fake_modrinth)
    monkeypatch.setattr(
        official_server_search,
        "search_curseforge_official_server",
        await fake_empty("curseforge"),
    )
    monkeypatch.setattr(
        official_server_search,
        "search_ftb_official_server",
        await fake_empty("ftb"),
    )

    parsed = ParsedQuery(query="ATM10", version_hint=None, source_hint=None)

    first_results, _ = await official_server_search.search_official_servers(parsed)
    second_results, _ = await official_server_search.search_official_servers(parsed)

    assert first_results == second_results
    assert calls == {"modrinth": 1, "curseforge": 1, "ftb": 1}
