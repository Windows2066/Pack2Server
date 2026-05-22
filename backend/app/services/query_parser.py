from pydantic import BaseModel


class ParsedQuery(BaseModel):
    query: str
    version_hint: str | None = None
    source_hint: str | None = None


SOURCE_HINTS = {
    "modrinth": "modrinth",
    "curseforge": "curseforge",
    "ftb": "ftb",
}


def parse_pack_query(text: str) -> ParsedQuery:
    normalized = " ".join(text.strip().split())
    lowered = normalized.lower()
    source_hint = next((value for key, value in SOURCE_HINTS.items() if key in lowered), None)
    version_hint = "latest" if any(word in normalized for word in ["最新版", "最新", "latest"]) else None

    query = normalized
    for token in ["我想要", "帮我找", "服务端", "最新版", "最新", "latest", "上", "的"]:
        query = query.replace(token, " ")
    for source in SOURCE_HINTS:
        query = query.replace(source, " ")
        query = query.replace(source.capitalize(), " ")
    query = " ".join(query.split()).strip()

    return ParsedQuery(query=query or normalized, version_hint=version_hint, source_hint=source_hint)
