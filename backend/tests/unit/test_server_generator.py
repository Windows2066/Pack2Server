import hashlib
import zipfile

import pytest

from app.core.config import get_settings
from app.services.archive_analyzer import ArchiveAnalysis, RemoteModFile
from app.services.server_generator import (
    RemoteFetchResult,
    RemoteModDownloadError,
    _fetch_remote_mod_file,
    build_runnable_server_artifact,
)


def test_build_runnable_server_artifact_creates_scripts_mods_and_archive(tmp_path):
    upload_archive = tmp_path / "pack.mrpack"
    with zipfile.ZipFile(upload_archive, "w") as archive:
        archive.writestr("mods/server-lib.jar", "server")
        archive.writestr("mods/journeymap-client.jar", "client")

    artifact = build_runnable_server_artifact(
        task_id="task-1",
        upload_archive=upload_archive,
        workspace_root=tmp_path / "workspaces",
        artifact_root=tmp_path / "artifacts",
        analysis=ArchiveAnalysis(
            pack_name="测试包",
            pack_version="1.0.0",
            minecraft_version="1.20.1",
            loader="fabric",
            mod_files=["mods/server-lib.jar", "mods/journeymap-client.jar"],
        ),
    )

    assert artifact.archive_path.exists()
    assert (artifact.workspace_path / "mods" / "server-lib.jar").exists()
    assert (artifact.workspace_path / "_disabled_client_mods" / "journeymap-client.jar").exists()
    assert (artifact.workspace_path / "start.sh").exists()
    assert (artifact.workspace_path / "start.bat").exists()
    assert (artifact.workspace_path / "eula.txt").read_text(encoding="utf-8") == "eula=false\n"

    with zipfile.ZipFile(artifact.archive_path) as archive:
        names = set(archive.namelist())

    assert "start.sh" in names
    assert "start.bat" in names
    assert "mods/server-lib.jar" in names
    assert "_disabled_client_mods/journeymap-client.jar" in names


def test_build_runnable_server_artifact_downloads_modrinth_remote_mods(tmp_path):
    upload_archive = tmp_path / "pack.mrpack"
    with zipfile.ZipFile(upload_archive, "w") as archive:
        archive.writestr("modrinth.index.json", "{}")

    server_bytes = b"server remote mod"
    client_bytes = b"client remote mod"

    def fetcher(remote_file: RemoteModFile) -> bytes:
        return {
            "mods/remote-lib.jar": server_bytes,
            "mods/journeymap-client.jar": client_bytes,
        }[remote_file.path]

    artifact = build_runnable_server_artifact(
        task_id="task-remote",
        upload_archive=upload_archive,
        workspace_root=tmp_path / "workspaces",
        artifact_root=tmp_path / "artifacts",
        analysis=ArchiveAnalysis(
            pack_name="remote pack",
            pack_version="1.0.0",
            minecraft_version="1.20.1",
            loader="fabric",
            mod_files=[],
            remote_mod_files=[
                RemoteModFile(
                    path="mods/remote-lib.jar",
                    downloads=["https://example.test/remote-lib.jar"],
                    hashes={"sha1": hashlib.sha1(server_bytes).hexdigest()},
                ),
                RemoteModFile(
                    path="mods/journeymap-client.jar",
                    downloads=["https://example.test/journeymap-client.jar"],
                    hashes={"sha1": hashlib.sha1(client_bytes).hexdigest()},
                ),
            ],
        ),
        remote_fetcher=fetcher,
    )

    assert (artifact.workspace_path / "mods" / "remote-lib.jar").read_bytes() == server_bytes
    assert (
        artifact.workspace_path / "_disabled_client_mods" / "journeymap-client.jar"
    ).read_bytes() == client_bytes
    assert artifact.kept_mods == 1
    assert artifact.disabled_mods == 1

    with zipfile.ZipFile(artifact.archive_path) as archive:
        names = set(archive.namelist())

    assert "mods/remote-lib.jar" in names
    assert "_disabled_client_mods/journeymap-client.jar" in names


def test_build_runnable_server_artifact_uses_curseforge_downloaded_file_name(tmp_path):
    upload_archive = tmp_path / "pack.zip"
    with zipfile.ZipFile(upload_archive, "w") as archive:
        archive.writestr("manifest.json", "{}")

    server_bytes = b"curseforge mod"

    artifact = build_runnable_server_artifact(
        task_id="task-cf",
        upload_archive=upload_archive,
        workspace_root=tmp_path / "workspaces",
        artifact_root=tmp_path / "artifacts",
        analysis=ArchiveAnalysis(
            pack_name="curse pack",
            pack_version="1.0.0",
            minecraft_version="1.20.1",
            loader="forge",
            mod_files=[],
            remote_mod_files=[
                RemoteModFile(
                    path="mods/238222-4613821.jar",
                    source="curseforge",
                    project_id=238222,
                    file_id=4613821,
                )
            ],
        ),
        remote_fetcher=lambda _remote_file: RemoteFetchResult(
            content=server_bytes,
            file_name="real-mod-file.jar",
        ),
    )

    assert (artifact.workspace_path / "mods" / "real-mod-file.jar").read_bytes() == server_bytes
    assert artifact.kept_mods == 1

    with zipfile.ZipFile(artifact.archive_path) as archive:
        names = set(archive.namelist())

    assert "mods/real-mod-file.jar" in names


def test_curseforge_remote_fetch_requires_api_key(monkeypatch):
    monkeypatch.delenv("CURSEFORGE_API_KEY", raising=False)
    monkeypatch.delenv("COUSEFORGE_API_KEY", raising=False)
    get_settings.cache_clear()

    try:
        with pytest.raises(RemoteModDownloadError, match="CURSEFORGE_API_KEY"):
            _fetch_remote_mod_file(
                RemoteModFile(
                    path="mods/238222-4613821.jar",
                    source="curseforge",
                    project_id=238222,
                    file_id=4613821,
                )
            )
    finally:
        get_settings.cache_clear()
