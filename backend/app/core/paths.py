from pathlib import Path

from app.core.config import get_settings


def data_root() -> Path:
    return get_settings().data_dir


def ensure_data_dirs() -> None:
    for name in ["uploads", "workspaces", "artifacts", "reports", "cache"]:
        (data_root() / name).mkdir(parents=True, exist_ok=True)


def safe_child_path(root: Path, child: str) -> Path:
    root_resolved = root.resolve()
    target = (root / child).resolve()
    if root_resolved != target and root_resolved not in target.parents:
        raise ValueError("路径超出允许范围")
    return target
