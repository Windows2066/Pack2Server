from pathlib import Path
from zipfile import ZipFile


def read_mod_id(jar_path: Path) -> str | None:
    with ZipFile(jar_path) as jar:
        if "fabric.mod.json" in jar.namelist():
            return jar.read("fabric.mod.json").decode("utf-8", errors="ignore")
        if "META-INF/mods.toml" in jar.namelist():
            return jar.read("META-INF/mods.toml").decode("utf-8", errors="ignore")
    return None
