import json
import zipfile
from dataclasses import dataclass
from pathlib import Path


class ArchiveSecurityError(ValueError):
    pass


@dataclass(frozen=True)
class ArchiveAnalysis:
    pack_name: str | None
    pack_version: str | None
    minecraft_version: str | None
    loader: str | None
    mod_files: list[str]


def _assert_safe_zip(archive: zipfile.ZipFile) -> None:
    for member in archive.infolist():
        path = Path(member.filename)
        if path.is_absolute() or ".." in path.parts:
            raise ArchiveSecurityError("压缩包包含不安全路径")


def _loader_from_dependencies(dependencies: dict[str, str]) -> str | None:
    for key in ["neoforge", "forge", "fabric-loader", "quilt-loader"]:
        if key in dependencies:
            return {"fabric-loader": "fabric", "quilt-loader": "quilt"}.get(key, key)
    return None


def analyze_archive(path: Path) -> ArchiveAnalysis:
    with zipfile.ZipFile(path) as archive:
        _assert_safe_zip(archive)
        names = archive.namelist()
        mod_files = [name for name in names if name.lower().endswith(".jar")]

        if "modrinth.index.json" in names:
            data = json.loads(archive.read("modrinth.index.json").decode("utf-8"))
            dependencies = data.get("dependencies", {})
            return ArchiveAnalysis(
                pack_name=data.get("name"),
                pack_version=data.get("versionId"),
                minecraft_version=dependencies.get("minecraft"),
                loader=_loader_from_dependencies(dependencies),
                mod_files=mod_files,
            )

        if "manifest.json" in names:
            data = json.loads(archive.read("manifest.json").decode("utf-8"))
            minecraft = data.get("minecraft", {})
            loaders = minecraft.get("modLoaders", [])
            loader_id = loaders[0].get("id") if loaders else None
            loader = loader_id.split("-")[0] if loader_id else None
            return ArchiveAnalysis(
                pack_name=data.get("name"),
                pack_version=data.get("version"),
                minecraft_version=minecraft.get("version"),
                loader=loader,
                mod_files=mod_files,
            )

        return ArchiveAnalysis(None, None, None, None, mod_files)
