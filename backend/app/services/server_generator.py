from pathlib import Path
import shutil


def create_server_workspace(workspace: Path, mod_files: list[Path]) -> Path:
    mods_dir = workspace / "mods"
    disabled_dir = workspace / "_disabled_client_mods"
    mods_dir.mkdir(parents=True, exist_ok=True)
    disabled_dir.mkdir(parents=True, exist_ok=True)
    for mod_file in mod_files:
        shutil.copy2(mod_file, mods_dir / mod_file.name)
    (workspace / "README.txt").write_text("请根据 start.bat 或 start.sh 启动服务端。\n", encoding="utf-8")
    return workspace
