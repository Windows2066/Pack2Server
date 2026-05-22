import re
from html.parser import HTMLParser

import httpx

from app.sources.models import SourceSearchResult


async def search_ftb_official_server(
    query: str,
    *,
    client: httpx.AsyncClient | None = None,
) -> list[SourceSearchResult]:
    if client is not None:
        return await _search_with_client(query, client)

    async with httpx.AsyncClient(
        base_url="https://feed-the-beast.com",
        timeout=10,
        headers={"User-Agent": "opc-mc-server-pack-builder/0.1"},
    ) as real_client:
        return await _search_with_client(query, real_client)


async def _search_with_client(query: str, client: httpx.AsyncClient) -> list[SourceSearchResult]:
    listing_response = await client.get("/modpacks/server-files/windows")
    listing_response.raise_for_status()
    links = _ServerFilesLinkParser.parse(listing_response.text)
    match = _best_link(query, links)
    if match is None:
        return []

    detail_response = await client.get(match.href)
    detail_response.raise_for_status()
    download_url = _extract_server_download_url(detail_response.text)
    if download_url is None:
        return []

    version = _extract_ftb_version_id(download_url)
    return [
        SourceSearchResult(
            source="ftb",
            pack_name=query,
            pack_version=version,
            minecraft_version=None,
            loader=None,
            download_url=download_url,
            match_reason="FTB Server Installer 页面包含官方 Server Installer 下载链接",
            confidence=0.76,
        )
    ]


class _ServerFileLink:
    def __init__(self, href: str, text: str) -> None:
        self.href = href
        self.text = text


class _ServerFilesLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[_ServerFileLink] = []
        self._current_href: str | None = None
        self._current_text: list[str] = []

    @classmethod
    def parse(cls, html: str) -> list[_ServerFileLink]:
        parser = cls()
        parser.feed(html)
        return parser.links

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href and "/modpacks/server-files/windows/" in href:
            self._current_href = href
            self._current_text = []

    def handle_data(self, data: str) -> None:
        if self._current_href:
            self._current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._current_href:
            self.links.append(_ServerFileLink(self._current_href, " ".join(self._current_text)))
            self._current_href = None
            self._current_text = []


def _best_link(query: str, links: list[_ServerFileLink]) -> _ServerFileLink | None:
    query_tokens = _tokens(query)
    for link in links:
        text = f"{link.text} {link.href}"
        if query_tokens and query_tokens.issubset(_tokens(text)):
            return link
    return None


def _tokens(text: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", text.lower()) if token}


def _extract_server_download_url(html: str) -> str | None:
    match = re.search(r"https://api\.feed-the-beast\.com/v1/modpacks/public/modpack/\d+/\d+/server/(?:windows|linux)", html)
    return match.group(0) if match else None


def _extract_ftb_version_id(download_url: str) -> str | None:
    match = re.search(r"/modpack/\d+/(\d+)/server/", download_url)
    return match.group(1) if match else None
