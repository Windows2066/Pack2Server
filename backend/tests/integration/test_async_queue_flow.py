import io
import zipfile

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.workers import queue as queue_module


class FakeQueue:
    def __init__(self):
        self.jobs = []

    def enqueue(self, func, *args):
        self.jobs.append((func.__name__, args))
        return {"queued": True}


def _mrpack_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("modrinth.index.json", '{"name":"异步包","dependencies":{"minecraft":"1.20.1"}}')
    return buffer.getvalue()


def test_upload_task_stays_queued_when_real_queue_enabled(monkeypatch):
    settings = get_settings()
    old_value = settings.run_jobs_inline
    fake_queue = FakeQueue()
    settings.run_jobs_inline = False
    monkeypatch.setattr(queue_module, "get_queue", lambda: fake_queue)
    client = TestClient(app)

    try:
        response = client.post(
            "/api/uploads",
            files={"file": ("pack.mrpack", _mrpack_bytes(), "application/octet-stream")},
        )
    finally:
        settings.run_jobs_inline = old_value

    assert response.status_code == 202
    task_id = response.json()["task_id"]
    assert fake_queue.jobs == [("run_upload_generate_task", (task_id,))]

    detail = client.get(f"/api/tasks/{task_id}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "queued"
