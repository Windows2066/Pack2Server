import json

import httpx
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.services.query_parser import parse_pack_query


class QueryCandidate(BaseModel):
    query: str
    version_hint: str | None = None
    source_hint: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


class QueryCandidateResponse(BaseModel):
    candidates: list[QueryCandidate]


async def parse_query_candidates(
    text: str,
    *,
    api_key: str | None = None,
    client: httpx.AsyncClient | None = None,
) -> list[QueryCandidate]:
    key = api_key if api_key is not None else get_settings().deepseek_api_key
    if not key:
        parsed = parse_pack_query(text)
        return [
            QueryCandidate(
                query=parsed.query,
                version_hint=parsed.version_hint,
                source_hint=parsed.source_hint,
                confidence=0.6,
                reason="未配置 DeepSeek API key，使用本地规则解析",
            )
        ]

    owns_client = client is None
    settings = get_settings()
    active_client = client or httpx.AsyncClient(base_url=settings.deepseek_base_url, timeout=20)
    try:
        response = await active_client.post(
            "/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": settings.deepseek_model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "你是 Minecraft 整合包检索助手。只返回 JSON，不要 Markdown。"
                            "JSON 结构为 {\"candidates\":[{\"query\":\"整合包名\","
                            "\"version_hint\":\"latest 或具体版本或 null\","
                            "\"source_hint\":\"curseforge/modrinth/ftb 或 null\","
                            "\"confidence\":0到1,\"reason\":\"中文理由\"}]}。"
                            "最多返回 3 个候选，优先保留用户原意。"
                        ),
                    },
                    {"role": "user", "content": text},
                ],
            },
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return QueryCandidateResponse.model_validate(json.loads(_strip_json_fence(content))).candidates
    except Exception:
        parsed = parse_pack_query(text)
        return [
            QueryCandidate(
                query=parsed.query,
                version_hint=parsed.version_hint,
                source_hint=parsed.source_hint,
                confidence=0.45,
                reason="DeepSeek 解析不可用，已回退到本地规则解析",
            )
        ]
    finally:
        if owns_client:
            await active_client.aclose()


def _strip_json_fence(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return stripped
