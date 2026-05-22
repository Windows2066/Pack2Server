import queue
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path


READY_MARKERS = (
    "Done (",
    "For help, type",
)


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    message: str
    log_excerpt: list[str]


def verify_startup(
    workspace: Path | None = None,
    *,
    enabled: bool,
    timeout_seconds: int = 900,
    java_executable: str = "java",
    command: list[str] | None = None,
) -> VerificationResult:
    if not enabled:
        return VerificationResult(True, "启动验证已跳过", [])

    if workspace is None:
        return VerificationResult(False, "启动验证缺少工作目录", ["workspace is required"])

    if not (workspace / "server.jar").is_file():
        return VerificationResult(
            False,
            "未找到 server.jar，无法执行启动验证",
            ["server.jar not found"],
        )

    process_command = command or [
        java_executable,
        "-Xms1G",
        "-Xmx2G",
        "-jar",
        "server.jar",
        "nogui",
    ]

    try:
        process = subprocess.Popen(
            process_command,
            cwd=workspace,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:
        return VerificationResult(False, "启动验证无法启动 Java 进程", [str(exc)])

    lines: list[str] = []
    output_queue: queue.Queue[str] = queue.Queue()
    reader = threading.Thread(target=_read_output, args=(process, output_queue), daemon=True)
    reader.start()

    deadline = time.monotonic() + timeout_seconds
    try:
        while time.monotonic() < deadline:
            try:
                line = output_queue.get(timeout=0.1).rstrip()
            except queue.Empty:
                if process.poll() is not None:
                    break
                continue

            if line:
                lines.append(line)
                if _line_indicates_ready(line):
                    _terminate_process(process)
                    return VerificationResult(True, "启动验证通过，服务端已进入 ready 状态", lines[-40:])

        while not output_queue.empty():
            line = output_queue.get_nowait().rstrip()
            if line:
                lines.append(line)

        if process.poll() is None:
            _terminate_process(process)
            return VerificationResult(False, "启动验证超时，服务端未进入 ready 状态", lines[-40:])

        return VerificationResult(False, "启动验证失败，服务端进程提前退出", lines[-40:])
    finally:
        if process.poll() is None:
            _terminate_process(process)


def _read_output(process: subprocess.Popen[str], output_queue: queue.Queue[str]) -> None:
    if process.stdout is None:
        return
    for line in process.stdout:
        output_queue.put(line)


def _line_indicates_ready(line: str) -> bool:
    return any(marker in line for marker in READY_MARKERS)


def _terminate_process(process: subprocess.Popen[str]) -> None:
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
