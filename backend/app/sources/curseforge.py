from app.core.config import get_settings
from app.sources.models import SourceSearchResult


async def search_curseforge_official_server(query: str) -> list[SourceSearchResult]:
    if not get_settings().curseforge_api_key:
        return []
    return [
        SourceSearchResult(
            source="curseforge",
            pack_name=query,
            pack_version="latest",
            minecraft_version=None,
            loader=None,
            download_url=None,
            match_reason="CurseForge API key 已配置，等待真实检索实现",
            confidence=0.5,
        )
    ]
