import io
import json
import zipfile

import pytest

from app.services.archive_analyzer import ArchiveSecurityError, analyze_archive
from app.services.artifact_access import resolve_artifact_path


def _zip_bytes(entries: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def test_rejects_path_traversal_archive(tmp_path):
    archive_path = tmp_path / "bad.zip"
    archive_path.write_bytes(_zip_bytes({"../evil.txt": "oops"}))

    with pytest.raises(ArchiveSecurityError):
        analyze_archive(archive_path)


def test_rejects_artifact_path_outside_data_root():
    with pytest.raises(ValueError):
        resolve_artifact_path("../secret.zip")


def test_reads_modrinth_index(tmp_path):
    archive_path = tmp_path / "pack.mrpack"
    archive_path.write_bytes(
        _zip_bytes(
            {
                "modrinth.index.json": '{"name":"测试包","versionId":"1.0.0","dependencies":{"minecraft":"1.20.1","forge":"47.2.0"},"files":[]}'
            }
        )
    )

    result = analyze_archive(archive_path)

    assert result.pack_name == "测试包"
    assert result.minecraft_version == "1.20.1"
    assert result.loader == "forge"


def test_reads_modrinth_remote_mod_files(tmp_path):
    archive_path = tmp_path / "pack.mrpack"
    archive_path.write_bytes(
        _zip_bytes(
            {
                "modrinth.index.json": json.dumps(
                    {
                        "name": "remote pack",
                        "versionId": "1.0.0",
                        "dependencies": {"minecraft": "1.20.1", "fabric-loader": "0.15.0"},
                        "files": [
                            {
                                "path": "mods/remote-lib.jar",
                                "downloads": [
                                    "https://cdn.modrinth.com/data/abc123/versions/def456/remote-lib.jar"
                                ],
                                "hashes": {"sha1": "abc123"},
                            },
                            {
                                "path": "resourcepacks/not-a-mod.zip",
                                "downloads": ["https://example.test/not-a-mod.zip"],
                            },
                        ],
                    }
                )
            }
        )
    )

    result = analyze_archive(archive_path)

    assert len(result.remote_mod_files) == 1
    remote_file = result.remote_mod_files[0]
    assert remote_file.path == "mods/remote-lib.jar"
    assert remote_file.source == "modrinth"
    assert remote_file.project_id == "abc123"
    assert remote_file.downloads == [
        "https://cdn.modrinth.com/data/abc123/versions/def456/remote-lib.jar"
    ]
    assert remote_file.hashes == {"sha1": "abc123"}


def test_reads_curseforge_manifest_remote_mod_files(tmp_path):
    archive_path = tmp_path / "pack.zip"
    archive_path.write_bytes(
        _zip_bytes(
            {
                "manifest.json": json.dumps(
                    {
                        "name": "curse pack",
                        "version": "1.0.0",
                        "minecraft": {
                            "version": "1.20.1",
                            "modLoaders": [{"id": "forge-47.2.0", "primary": True}],
                        },
                        "files": [
                            {"projectID": 238222, "fileID": 4613821, "required": True},
                            {"projectID": 238223, "fileID": 4613822, "required": False},
                        ],
                    }
                )
            }
        )
    )

    result = analyze_archive(archive_path)

    assert len(result.remote_mod_files) == 1
    remote_file = result.remote_mod_files[0]
    assert remote_file.source == "curseforge"
    assert remote_file.project_id == 238222
    assert remote_file.file_id == 4613821
    assert remote_file.path == "mods/238222-4613821.jar"
