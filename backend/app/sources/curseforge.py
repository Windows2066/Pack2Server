from collections.abc import Sequence

import httpx

from app.core.config import get_settings
from app.sources.models import SourceSearchResult

MINECRAFT_GAME_ID = 432
MODPACK_CLASS_ID = 4471


async def search_curseforge_official_server(
    query: str,
    *,
    version_hint: str | None = None,
    api_key: str | None = None,
    client: httpx.AsyncClient | None = None,
) -> list[SourceSearchResult]:
    api_key = api_key if api_key is not None else get_settings().curseforge_api_key
    if not api_key:
        return []

    if client is not None:
        return await _search_with_client(query, version_hint, api_key, client)

    async with httpx.AsyncClient(
        base_url="https://api.curseforge.com",
        timeout=10,
        headers={"x-api-key": api_key, "Accept": "application/json"},
    ) as real_client:
        return await _search_with_client(query, version_hint, api_key, real_client)


async def _search_with_client(
    query: str,
    version_hint: str | None,
    api_key: str,
    client: httpx.AsyncClient,
) -> list[SourceSearchResult]:
    search_response = await client.get(
        "/v1/mods/search",
        params={
            "gameId": MINECRAFT_GAME_ID,
            "classId": MODPACK_CLASS_ID,
            "searchFilter": query,
            "pageSize": 5,
        },
        headers={"x-api-key": api_key},
    )
    search_response.raise_for_status()
    mods = search_response.json().get("data", [])

    results: list[SourceSearchResult] = []
    for mod in mods:
        mod_id = mod.get("id")
        if mod_id is None:
            continue
        files_response = await client.get(
            f"/v1/mods/{mod_id}/files",
            params={"pageSize": 20},
            headers={"x-api-key": api_key},
        )
        files_response.raise_for_status()
        files = _prioritized_files(files_response.json().get("data", []), version_hint)
        result = await _server_result_from_files(query, mod, files, api_key, client)
        if result is not None:
            results.append(result)
    return results


async def _server_result_from_files(
    query: str,
    mod: dict,
    files: list[dict],
    api_key: str,
    client: httpx.AsyncClient,
) -> SourceSearchResult | None:
    for file_info in files:
        if file_info.get("isServerPack") and file_info.get("downloadUrl"):
            return _to_result(query, mod, file_info, "CurseForge 文件标记为 isServerPack")

        server_pack_file_id = file_info.get("serverPackFileId")
        if server_pack_file_id:
            response = await client.get(
                f"/v1/mods/{mod['id']}/files/{server_pack_file_id}",
                headers={"x-api-key": api_key},
            )
            response.raise_for_status()
            server_file = response.json().get("data", {})
            if server_file.get("downloadUrl"):
                return _to_result(query, mod, server_file, f"CurseForge client 文件提供 serverPackFileId={server_pack_file_id}")
    return None


def _to_result(query: str, mod: dict, file_info: dict, reason: str) -> SourceSearchResult:
    game_versions = file_info.get("gameVersions", [])
    return SourceSearchResult(
        source="curseforge",
        pack_name=mod.get("name") or query,
        pack_version=file_info.get("displayName") or file_info.get("fileName"),
        minecraft_version=_minecraft_version(game_versions),
        loader=_loader(game_versions),
        download_url=file_info.get("downloadUrl"),
        match_reason=reason,
        confidence=0.9,
    )


def _prioritized_files(files: list[dict], version_hint: str | None) -> list[dict]:
    if not version_hint or version_hint == "latest":
        return files
    lowered = version_hint.lower()
    return sorted(
        files,
        key=lambda item: lowered not in f"{item.get('displayName', '')} {item.get('fileName', '')}".lower(),
    )


def _minecraft_version(game_versions: Sequence[str]) -> str | None:
    for value in game_versions:
        if value[:1].isdigit():
            return value
    return None


def _loader(game_versions: Sequence[str]) -> str | None:
    known = {"forge", "fabric", "neoforge", "quilt"}
    for value in game_versions:
        lowered = value.lower()
        if lowered in known:
            return lowered
    return None
