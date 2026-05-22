from app.services.query_parser import ParsedQuery
from app.sources.curseforge import search_curseforge_official_server
from app.sources.ftb import search_ftb_official_server
from app.sources.modrinth import search_modrinth_official_server
from app.sources.models import SourceSearchResult


async def search_official_servers(parsed: ParsedQuery) -> tuple[list[SourceSearchResult], list[str]]:
    searched = ["CurseForge", "Modrinth", "FTB"]
    results: list[SourceSearchResult] = []
    results.extend(await search_modrinth_official_server(parsed.query))
    results.extend(await search_curseforge_official_server(parsed.query))
    results.extend(await search_ftb_official_server(parsed.query))
    return results, searched
