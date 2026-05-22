from pydantic import BaseModel


class OfficialServerCandidateRead(BaseModel):
    source: str
    pack_name: str
    pack_version: str | None = None
    minecraft_version: str | None = None
    loader: str | None = None
    download_url: str | None = None
    match_reason: str
    confidence: float
