from pathlib import Path

from app.core.paths import data_root, safe_child_path


def resolve_artifact_path(relative_path: str) -> Path:
    return safe_child_path(data_root() / "artifacts", relative_path)
