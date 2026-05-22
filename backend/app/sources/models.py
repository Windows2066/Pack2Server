from dataclasses import dataclass


@dataclass(frozen=True)
class SourceSearchResult:
    source: str
    pack_name: str
    pack_version: str | None
    minecraft_version: str | None
    loader: str | None
    download_url: str | None
    match_reason: str
    confidence: float
