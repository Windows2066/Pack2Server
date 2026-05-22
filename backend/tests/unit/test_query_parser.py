from app.services.query_parser import parse_pack_query


def test_parse_latest_pack_query_extracts_version_hint():
    parsed = parse_pack_query("我想要 ATM10 最新版服务端")

    assert parsed.query == "ATM10"
    assert parsed.version_hint == "latest"
    assert parsed.source_hint is None


def test_parse_source_hint_for_modrinth():
    parsed = parse_pack_query("帮我找 Modrinth 上 fabulously optimized 的服务端")

    assert parsed.query == "fabulously optimized"
    assert parsed.source_hint == "modrinth"
