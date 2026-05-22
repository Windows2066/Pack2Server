import io
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
