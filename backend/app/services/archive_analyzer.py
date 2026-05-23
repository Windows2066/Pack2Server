import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path


class ArchiveSecurityError(ValueError):
    pass


@dataclass(frozen=True)
class RemoteModFile:
    path: str
    downloads: list[str] = field(default_factory=list)
    hashes: dict[str, str] = field(default_factory=dict)
    source: str = "direct"
    project_id: int | None = None
    file_id: int | None = None
    required: bool = True


@dataclass(frozen=True)
class ArchiveAnalysis:
    pack_name: str | None
    pack_version: str | None
    minecraft_version: str | None
    loader: str | None
    mod_files: list[str]
    remote_mod_files: list[RemoteModFile] = field(default_factory=list)


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
                remote_mod_files=_remote_mod_files_from_modrinth(data),
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
                remote_mod_files=_remote_mod_files_from_curseforge(data),
            )

        return ArchiveAnalysis(None, None, None, None, mod_files)


def _remote_mod_files_from_modrinth(data: dict) -> list[RemoteModFile]:
    remote_files: list[RemoteModFile] = []
    for item in data.get("files", []):
        if not isinstance(item, dict):
            continue

        path = item.get("path")
        if not isinstance(path, str) or not path.lower().endswith(".jar"):
            continue

        downloads = item.get("downloads", [])
        if not isinstance(downloads, list):
            downloads = []
        downloads = [url for url in downloads if isinstance(url, str)]

        hashes = item.get("hashes", {})
        if not isinstance(hashes, dict):
            hashes = {}
        hashes = {str(key): str(value) for key, value in hashes.items()}

        remote_files.append(RemoteModFile(path=path, downloads=downloads, hashes=hashes))

    return remote_files


def _remote_mod_files_from_curseforge(data: dict) -> list[RemoteModFile]:
    remote_files: list[RemoteModFile] = []
    for item in data.get("files", []):
        if not isinstance(item, dict):
            continue
        if item.get("required") is False:
            continue

        project_id = _coerce_int(item.get("projectID"))
        file_id = _coerce_int(item.get("fileID"))
        if project_id is None or file_id is None:
            continue

        remote_files.append(
            RemoteModFile(
                path=f"mods/{project_id}-{file_id}.jar",
                source="curseforge",
                project_id=project_id,
                file_id=file_id,
                required=item.get("required", True) is not False,
            )
        )

    return remote_files


def _coerce_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None
