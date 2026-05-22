import httpx
import pytest

from app.sources.curseforge import search_curseforge_official_server
from app.sources.ftb import search_ftb_official_server
from app.sources.modrinth import search_modrinth_official_server


@pytest.mark.asyncio
async def test_modrinth_finds_server_named_version_file():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v2/search":
            return httpx.Response(
                200,
                json={
                    "hits": [
                        {
                            "project_id": "project-1",
                            "slug": "example-pack",
                            "title": "Example Pack",
                            "latest_version": "1.20.1",
                        }
                    ]
                },
            )
        if request.url.path == "/v2/project/project-1/version":
            return httpx.Response(
                200,
                json=[
                    {
                        "name": "Server 1.0.0",
                        "version_number": "1.0.0",
                        "game_versions": ["1.20.1"],
                        "loaders": ["forge"],
                        "files": [
                            {
                                "filename": "example-pack-server-1.0.0.zip",
                                "url": "https://cdn.modrinth.com/example-pack-server.zip",
                                "primary": True,
                            }
                        ],
                    }
                ],
            )
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://api.modrinth.com") as client:
        results = await search_modrinth_official_server("Example Pack", client=client, use_fixtures=False)

    assert len(results) == 1
    assert results[0].source == "modrinth"
    assert results[0].pack_name == "Example Pack"
    assert results[0].pack_version == "1.0.0"
    assert results[0].minecraft_version == "1.20.1"
    assert results[0].loader == "forge"
    assert results[0].download_url == "https://cdn.modrinth.com/example-pack-server.zip"
    assert "服务端文件" in results[0].match_reason


@pytest.mark.asyncio
async def test_curseforge_follows_server_pack_file_id():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/mods/search":
            return httpx.Response(200, json={"data": [{"id": 42, "name": "Example Pack"}]})
        if request.url.path == "/v1/mods/42/files":
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": 100,
                            "displayName": "Client 1.0.0",
                            "fileName": "example-client.zip",
                            "gameVersions": ["1.20.1", "Forge"],
                            "serverPackFileId": 101,
                        }
                    ]
                },
            )
        if request.url.path == "/v1/mods/42/files/101":
            return httpx.Response(
                200,
                json={
                    "data": {
                        "id": 101,
                        "displayName": "Server 1.0.0",
                        "fileName": "example-server.zip",
                        "downloadUrl": "https://mediafilez.forgecdn.net/example-server.zip",
                        "gameVersions": ["1.20.1", "Forge"],
                        "isServerPack": True,
                    }
                },
            )
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://api.curseforge.com") as client:
        results = await search_curseforge_official_server(
            "Example Pack",
            api_key="secret",
            client=client,
        )

    assert len(results) == 1
    assert results[0].source == "curseforge"
    assert results[0].pack_name == "Example Pack"
    assert results[0].pack_version == "Server 1.0.0"
    assert results[0].minecraft_version == "1.20.1"
    assert results[0].loader == "forge"
    assert results[0].download_url == "https://mediafilez.forgecdn.net/example-server.zip"
    assert "serverPackFileId" in results[0].match_reason


@pytest.mark.asyncio
async def test_ftb_extracts_server_installer_from_server_files_page():
    listing_html = """
    <a href="/modpacks/server-files/windows/28-ftb-beyond">
      FTB Beyond Magic Tech 28 1.11.0 1.10.2 Forge
    </a>
    """
    detail_html = """
    <h1>Server Files</h1>
    <a href="https://api.feed-the-beast.com/v1/modpacks/public/modpack/28/115/server/windows">Download for Windows</a>
    <code>Invoke-WebRequest -Uri "https://api.feed-the-beast.com/v1/modpacks/public/modpack/28/115/server/windows"</code>
    """

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/modpacks/server-files/windows":
            return httpx.Response(200, text=listing_html)
        if request.url.path == "/modpacks/server-files/windows/28-ftb-beyond":
            return httpx.Response(200, text=detail_html)
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://feed-the-beast.com") as client:
        results = await search_ftb_official_server("FTB Beyond", client=client)

    assert len(results) == 1
    assert results[0].source == "ftb"
    assert results[0].pack_name == "FTB Beyond"
    assert results[0].pack_version == "115"
    assert results[0].download_url == "https://api.feed-the-beast.com/v1/modpacks/public/modpack/28/115/server/windows"
    assert "Server Installer" in results[0].match_reason
