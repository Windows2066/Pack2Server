from collections.abc import Sequence

import httpx

from app.core.config import get_settings
from app.sources.models import SourceSearchResult

SERVER_FILE_MARKERS = ("server", "serverpack", "server-pack", "server_pack")


async def search_modrinth_official_server(
    query: str,
    *,
    version_hint: str | None = None,
    client: httpx.AsyncClient | None = None,
    use_fixtures: bool | None = None,
) -> list[SourceSearchResult]:
    if use_fixtures is None:
        use_fixtures = get_settings().use_fixtures
    if use_fixtures:
        return _fixture_result(query)

    if client is not None:
        return await _search_with_client(query, version_hint, client)

    async with httpx.AsyncClient(
        base_url="https://api.modrinth.com",
        timeout=10,
        headers={"User-Agent": "opc-mc-server-pack-builder/0.1"},
    ) as real_client:
        return await _search_with_client(query, version_hint, real_client)


def _fixture_result(query: str) -> list[SourceSearchResult]:
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


async def _search_with_client(
    query: str,
    version_hint: str | None,
    client: httpx.AsyncClient,
) -> list[SourceSearchResult]:
    search_response = await client.get(
        "/v2/search",
        params={
            "query": query,
            "facets": '[["project_type:modpack"]]',
            "limit": 5,
        },
    )
    search_response.raise_for_status()
    projects = search_response.json().get("hits", [])

    results: list[SourceSearchResult] = []
    for project in projects:
        project_id = project.get("project_id") or project.get("slug")
        if not project_id:
            continue
        versions_response = await client.get(f"/v2/project/{project_id}/version")
        versions_response.raise_for_status()
        for version in _prioritized_versions(versions_response.json(), version_hint):
            server_file = _pick_server_file(version.get("files", []))
            if server_file is None:
                continue
            results.append(
                SourceSearchResult(
                    source="modrinth",
                    pack_name=project.get("title") or project.get("slug") or query,
                    pack_version=version.get("version_number") or version.get("name"),
                    minecraft_version=_first(version.get("game_versions")),
                    loader=_first(version.get("loaders")),
                    download_url=server_file.get("url"),
                    match_reason=f"Modrinth 版本文件包含服务端文件：{server_file.get('filename')}",
                    confidence=0.82,
                )
            )
            break
    return results


def _prioritized_versions(versions: list[dict], version_hint: str | None) -> list[dict]:
    if not version_hint or version_hint == "latest":
        return versions
    lowered = version_hint.lower()
    return sorted(
        versions,
        key=lambda item: lowered not in f"{item.get('name', '')} {item.get('version_number', '')}".lower(),
    )


def _pick_server_file(files: Sequence[dict]) -> dict | None:
    for file_info in files:
        filename = str(file_info.get("filename", "")).lower()
        if any(marker in filename for marker in SERVER_FILE_MARKERS) and file_info.get("url"):
            return file_info
    return None


def _first(values: Sequence[str] | None) -> str | None:
    return values[0] if values else None
