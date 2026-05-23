import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from app.core.paths import data_root
from app.services.mod_metadata import ModJarMetadata, read_mod_metadata


@dataclass(frozen=True)
class ModSideRule:
    match: list[str]
    decision: str
    confidence: float
    reason: str
    source: str = "builtin_rule"


@dataclass(frozen=True)
class ModSideDecision:
    decision: str
    confidence: float
    reason: str
    evidence_source: str
    matched_rule: str | None = None
    mod_id: str | None = None


def load_mod_side_rules(local_rules_path: Path | None = None) -> list[ModSideRule]:
    return [
        *load_builtin_mod_side_rules(),
        *load_local_mod_side_rules(local_rules_path),
    ]


def load_builtin_mod_side_rules() -> list[ModSideRule]:
    path = Path(__file__).parent / "rules" / "mod_side_rules.json"
    return _read_rules(path, source="builtin_rule")


def load_local_mod_side_rules(local_rules_path: Path | None = None) -> list[ModSideRule]:
    path = local_rules_path or data_root() / "rules" / "local_mod_side_rules.json"
    return _read_rules(path, source="local_rule")


def decide_mod_side_detailed(
    mod_id_or_filename: str,
    *,
    metadata: ModJarMetadata | None = None,
    jar_path: Path | None = None,
    local_rules_path: Path | None = None,
) -> ModSideDecision:
    metadata = metadata or (read_mod_metadata(jar_path) if jar_path else None)
    metadata_decision = _decision_from_metadata(metadata)
    if metadata_decision is not None:
        return metadata_decision

    target_values = _target_values(mod_id_or_filename, metadata)
    for rule in load_mod_side_rules(local_rules_path):
        matched = _first_matching_rule_value(rule, target_values)
        if matched:
            return ModSideDecision(
                decision=rule.decision,
                confidence=rule.confidence,
                reason=rule.reason,
                evidence_source=rule.source,
                matched_rule=matched,
                mod_id=metadata.mod_id if metadata else None,
            )

    return ModSideDecision(
        decision="keep_unknown",
        confidence=0.4,
        reason="未找到明确端侧证据，暂时保留并标记不确定",
        evidence_source="unknown",
        mod_id=metadata.mod_id if metadata else None,
    )


def decide_mod_side(mod_id_or_filename: str) -> tuple[str, float, str]:
    decision = decide_mod_side_detailed(mod_id_or_filename)
    return decision.decision, decision.confidence, decision.reason


def _decision_from_metadata(metadata: ModJarMetadata | None) -> ModSideDecision | None:
    if metadata is None or metadata.environment is None:
        return None
    if metadata.environment == "client":
        return ModSideDecision(
            decision="disable_client_only",
            confidence=0.98,
            reason=f"jar 元数据 {metadata.source} 标记 environment=client",
            evidence_source="jar_metadata",
            mod_id=metadata.mod_id,
        )
    if metadata.environment in {"server", "*"}:
        return ModSideDecision(
            decision="keep_server",
            confidence=0.82,
            reason=f"jar 元数据 {metadata.source} 标记 environment={metadata.environment}",
            evidence_source="jar_metadata",
            mod_id=metadata.mod_id,
        )
    return None


def _target_values(mod_id_or_filename: str, metadata: ModJarMetadata | None) -> list[str]:
    values = [mod_id_or_filename.lower()]
    if metadata:
        for value in [metadata.mod_id, metadata.name]:
            if value:
                values.append(value.lower())
    return values


def _first_matching_rule_value(rule: ModSideRule, target_values: Iterable[str]) -> str | None:
    lowered_matches = [item.lower() for item in rule.match]
    for target in target_values:
        for matcher in lowered_matches:
            if matcher and matcher in target:
                return matcher
    return None


def _read_rules(path: Path, *, source: str) -> list[ModSideRule]:
    if not path.exists():
        return []
    try:
        raw_rules = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return []
    if not isinstance(raw_rules, list):
        return []
    rules: list[ModSideRule] = []
    for raw_rule in raw_rules:
        if not isinstance(raw_rule, dict):
            continue
        match = raw_rule.get("match")
        if isinstance(match, str):
            match_values = [match]
        elif isinstance(match, list):
            match_values = [item for item in match if isinstance(item, str)]
        else:
            continue
        decision = raw_rule.get("decision")
        reason = raw_rule.get("reason")
        if not isinstance(decision, str) or not isinstance(reason, str):
            continue
        rules.append(
            ModSideRule(
                match=match_values,
                decision=decision,
                confidence=float(raw_rule.get("confidence", 0.8)),
                reason=reason,
                source=str(raw_rule.get("source") or source),
            )
        )
    return rules
