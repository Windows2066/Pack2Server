import io
import zipfile

from fastapi.testclient import TestClient

from app.api.routes_tasks import TASKS
from app.main import app


def _mrpack_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "modrinth.index.json",
            '{"name":"测试包","versionId":"1.0.0","dependencies":{"minecraft":"1.20.1","fabric-loader":"0.15.0"},"files":[]}',
        )
        archive.writestr("mods/server-lib.jar", "server")
        archive.writestr("mods/journeymap-client.jar", "client")
    return buffer.getvalue()


def test_upload_creates_generation_task():
    client = TestClient(app)

    response = client.post(
        "/api/uploads",
        files={"file": ("pack.mrpack", _mrpack_bytes(), "application/octet-stream")},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert "生成任务已创建" in body["message"]

    detail = client.get(f"/api/tasks/{body['task_id']}")
    assert detail.status_code == 200
    detail_body = detail.json()
    assert detail_body["status"] == "succeeded"
    assert detail_body["stage"] == "completed"
    assert detail_body["pack_identity"]["minecraft_version"] == "1.20.1"
    assert "服务端生成完成" in detail_body["report"]
    assert "启动验证已跳过" in detail_body["report"]
    assert detail_body["artifacts"]

    artifact = detail_body["artifacts"][0]
    download = client.get(f"/api/tasks/{body['task_id']}/artifacts/{artifact['id']}/download")
    assert download.status_code == 200

    with zipfile.ZipFile(io.BytesIO(download.content)) as archive:
        names = set(archive.namelist())

    assert "start.sh" in names
    assert "start.bat" in names
    assert "VERIFICATION.md" in names
    assert "mods/server-lib.jar" in names
    assert "_disabled_client_mods/journeymap-client.jar" in names

    TASKS.clear()
    persisted_detail = client.get(f"/api/tasks/{body['task_id']}")
    assert persisted_detail.status_code == 200
    assert persisted_detail.json()["status"] == "succeeded"
