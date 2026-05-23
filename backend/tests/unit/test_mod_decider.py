import json

from app.services.mod_decider import PlatformModSideEvidence, decide_mod_side_detailed
from app.services.mod_metadata import ModJarMetadata


def test_decides_known_client_only_mods_from_builtin_rules():
    decision = decide_mod_side_detailed("XaerosWorldMap_1.39.0.jar")

    assert decision.decision == "disable_client_only"
    assert decision.evidence_source == "builtin_rule"
    assert decision.confidence >= 0.9
    assert "Xaero" in decision.reason or "地图" in decision.reason


def test_jar_metadata_takes_priority_over_local_rules(tmp_path):
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "local_mod_side_rules.json").write_text(
        json.dumps(
            [
                {
                    "match": ["client-env-mod"],
                    "decision": "keep_server",
                    "confidence": 0.99,
                    "reason": "用户误配置的本地规则",
                }
            ]
        ),
        encoding="utf-8",
    )

    decision = decide_mod_side_detailed(
        "client-env-mod.jar",
        metadata=ModJarMetadata(mod_id="client-env-mod", environment="client"),
        local_rules_path=rules_dir / "local_mod_side_rules.json",
    )

    assert decision.decision == "disable_client_only"
    assert decision.evidence_source == "jar_metadata"


def test_curseforge_platform_metadata_has_priority_over_modrinth_and_jar_metadata():
    decision = decide_mod_side_detailed(
        "client-env-mod.jar",
        metadata=ModJarMetadata(mod_id="client-env-mod", environment="client"),
        platform_evidence=[
            PlatformModSideEvidence(
                source="modrinth_metadata",
                decision="disable_client_only",
                confidence=0.96,
                reason="Modrinth 标记 server_side=unsupported",
            ),
            PlatformModSideEvidence(
                source="curseforge_metadata",
                decision="keep_server",
                confidence=0.9,
                reason="CurseForge 项目元数据命中服务端保留规则",
            ),
        ],
    )

    assert decision.decision == "keep_server"
    assert decision.evidence_source == "curseforge_metadata"


def test_reads_user_confirmed_local_rules(tmp_path):
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "local_mod_side_rules.json").write_text(
        json.dumps(
            [
                {
                    "match": ["custom-client-tool"],
                    "decision": "disable_client_only",
                    "confidence": 0.88,
                    "reason": "用户确认该工具仅客户端有效",
                }
            ]
        ),
        encoding="utf-8",
    )

    decision = decide_mod_side_detailed(
        "custom-client-tool-1.0.jar",
        local_rules_path=rules_dir / "local_mod_side_rules.json",
    )

    assert decision.decision == "disable_client_only"
    assert decision.evidence_source == "local_rule"
    assert "用户确认" in decision.reason


def test_malformed_local_rules_fall_back_to_unknown(tmp_path):
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "local_mod_side_rules.json").write_text("{bad json", encoding="utf-8")

    decision = decide_mod_side_detailed(
        "unlisted-mod.jar",
        local_rules_path=rules_dir / "local_mod_side_rules.json",
    )

    assert decision.decision == "keep_unknown"
    assert decision.evidence_source == "unknown"
