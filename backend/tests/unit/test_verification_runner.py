import sys

from app.services.verification_runner import verify_startup


def test_verify_startup_detects_ready_log(tmp_path):
    server_jar = tmp_path / "server.jar"
    server_jar.write_text("fake", encoding="utf-8")
    fake_server = tmp_path / "fake_server.py"
    fake_server.write_text(
        "\n".join(
            [
                "import time",
                "print('Starting minecraft server version 1.20.1', flush=True)",
                "print('Done (1.234s)! For help, type \"help\"', flush=True)",
                "time.sleep(30)",
            ]
        ),
        encoding="utf-8",
    )

    result = verify_startup(
        workspace=tmp_path,
        enabled=True,
        timeout_seconds=5,
        command=[sys.executable, str(fake_server)],
    )

    assert result.ok is True
    assert "启动验证通过" in result.message
    assert any("Done" in line for line in result.log_excerpt)


def test_verify_startup_reports_missing_server_jar(tmp_path):
    result = verify_startup(workspace=tmp_path, enabled=True, timeout_seconds=1)

    assert result.ok is False
    assert "未找到 server.jar" in result.message
    assert result.log_excerpt
