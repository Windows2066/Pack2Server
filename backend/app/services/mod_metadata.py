import json
import tomllib
from dataclasses import dataclass
from pathlib import Path
from zipfile import BadZipFile, ZipFile


@dataclass(frozen=True)
class ModJarMetadata:
    mod_id: str | None = None
    name: str | None = None
    version: str | None = None
    environment: str | None = None
    source: str | None = None


def read_mod_id(jar_path: Path) -> str | None:
    metadata = read_mod_metadata(jar_path)
    return metadata.mod_id if metadata else None


def read_mod_metadata(jar_path: Path) -> ModJarMetadata | None:
    try:
        with ZipFile(jar_path) as jar:
            names = set(jar.namelist())
            if "fabric.mod.json" in names:
                return _read_fabric_like_metadata(jar, "fabric.mod.json")
            if "quilt.mod.json" in names:
                return _read_quilt_metadata(jar)
            if "META-INF/mods.toml" in names:
                return _read_toml_metadata(jar, "META-INF/mods.toml")
            if "META-INF/neoforge.mods.toml" in names:
                return _read_toml_metadata(jar, "META-INF/neoforge.mods.toml")
    except (BadZipFile, OSError, json.JSONDecodeError, tomllib.TOMLDecodeError, UnicodeDecodeError):
        return None
    return None


def _read_fabric_like_metadata(jar: ZipFile, name: str) -> ModJarMetadata:
    data = json.loads(jar.read(name).decode("utf-8"))
    return ModJarMetadata(
        mod_id=_string_or_none(data.get("id")),
        name=_string_or_none(data.get("name")),
        version=_string_or_none(data.get("version")),
        environment=_normalize_environment(data.get("environment")),
        source=name,
    )


def _read_quilt_metadata(jar: ZipFile) -> ModJarMetadata:
    data = json.loads(jar.read("quilt.mod.json").decode("utf-8"))
    loader = data.get("quilt_loader", {}) if isinstance(data.get("quilt_loader"), dict) else {}
    metadata = loader.get("metadata", {}) if isinstance(loader.get("metadata"), dict) else {}
    return ModJarMetadata(
        mod_id=_string_or_none(loader.get("id") or data.get("id")),
        name=_string_or_none(metadata.get("name") or data.get("name")),
        version=_string_or_none(loader.get("version") or data.get("version")),
        environment=_normalize_environment(data.get("environment") or loader.get("environment")),
        source="quilt.mod.json",
    )


def _read_toml_metadata(jar: ZipFile, name: str) -> ModJarMetadata | None:
    data = tomllib.loads(jar.read(name).decode("utf-8"))
    mods = data.get("mods", [])
    if not isinstance(mods, list) or not mods or not isinstance(mods[0], dict):
        return ModJarMetadata(source=name)
    first = mods[0]
    return ModJarMetadata(
        mod_id=_string_or_none(first.get("modId")),
        name=_string_or_none(first.get("displayName")),
        version=_string_or_none(first.get("version")),
        environment=_normalize_environment(first.get("environment")),
        source=name,
    )


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _normalize_environment(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    lowered = value.lower()
    if lowered in {"client", "server", "*"}:
        return lowered
    return lowered
