from pydantic import BaseModel


class PackIdentityRead(BaseModel):
    source: str = "unknown"
    pack_name: str | None = None
    pack_version: str | None = None
    minecraft_version: str | None = None
    loader: str | None = None
    confidence: float = 0.0
