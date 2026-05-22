from app.services.query_parser import ParsedQuery
from app.sources.curseforge import search_curseforge_official_server
from app.sources.ftb import search_ftb_official_server
from app.sources.modrinth import search_modrinth_official_server
from app.sources.models import SourceSearchResult

_CACHE: dict[str, tuple[list[SourceSearchResult], list[str]]] = {}


async def search_official_servers(parsed: ParsedQuery) -> tuple[list[SourceSearchResult], list[str]]:
    cache_key = f"{parsed.query.strip().lower()}:{parsed.version_hint or ''}:{parsed.source_hint or ''}"
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    searched = ["CurseForge", "Modrinth", "FTB"]
    results: list[SourceSearchResult] = []
    results.extend(await _safe_source_call(search_modrinth_official_server, parsed.query, version_hint=parsed.version_hint))
    results.extend(await _safe_source_call(search_curseforge_official_server, parsed.query, version_hint=parsed.version_hint))
    results.extend(await _safe_source_call(search_ftb_official_server, parsed.query))
    _CACHE[cache_key] = (results, searched)
    return _CACHE[cache_key]


def clear_official_server_cache() -> None:
    _CACHE.clear()


async def _safe_source_call(source_func, query: str, **kwargs) -> list[SourceSearchResult]:
    try:
        return await source_func(query, **kwargs)
    except Exception:
        return []
