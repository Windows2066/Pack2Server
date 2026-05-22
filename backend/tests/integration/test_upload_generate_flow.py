import io
import zipfile

from fastapi.testclient import TestClient

from app.main import app


def _mrpack_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "modrinth.index.json",
            '{"name":"测试包","versionId":"1.0.0","dependencies":{"minecraft":"1.20.1","fabric-loader":"0.15.0"},"files":[]}',
        )
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
