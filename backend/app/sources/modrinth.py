from app.sources.models import SourceSearchResult


async def search_modrinth_official_server(query: str) -> list[SourceSearchResult]:
    if "未找到" in query:
        return []
    return [
        SourceSearchResult(
            source="modrinth",
            pack_name=query,
            pack_version="latest",
            minecraft_version=None,
            loader=None,
            download_url=None,
            match_reason="样例模式下的 Modrinth 候选",
            confidence=0.6,
        )
    ]
