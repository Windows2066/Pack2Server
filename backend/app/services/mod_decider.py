import json
from pathlib import Path


def load_client_mod_rules() -> set[str]:
    path = Path(__file__).parent / "rules" / "client_mods.json"
    return set(json.loads(path.read_text(encoding="utf-8")))


def decide_mod_side(mod_id_or_filename: str) -> tuple[str, float, str]:
    lowered = mod_id_or_filename.lower()
    for rule in load_client_mod_rules():
        if rule in lowered:
            return "disable_client_only", 0.9, f"命中客户端专用规则：{rule}"
    return "keep_unknown", 0.4, "未找到明确端侧证据，暂时保留并标记不确定"
