import zipfile

from app.services.archive_analyzer import ArchiveAnalysis
from app.services.server_generator import build_runnable_server_artifact


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
