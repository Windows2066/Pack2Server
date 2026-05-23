import hashlib
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable

import httpx

from app.core.config import get_settings
from app.services.archive_analyzer import ArchiveAnalysis, ArchiveSecurityError, RemoteModFile
from app.services.mod_decider import decide_mod_side
from app.services.verification_runner import VerificationResult


COPYABLE_DIRECTORIES = {
    "config",
    "defaultconfigs",
    "kubejs",
    "scripts",
    "serverconfig",
}


@dataclass(frozen=True)
class GeneratedServerArtifact:
    workspace_path: Path
    archive_path: Path
    kept_mods: int
    disabled_mods: int


@dataclass(frozen=True)
class RemoteFetchResult:
    content: bytes
    file_name: str | None = None


class RemoteModDownloadError(RuntimeError):
    pass


def create_server_workspace(workspace: Path, mod_files: list[Path]) -> Path:
    mods_dir = workspace / "mods"
    disabled_dir = workspace / "_disabled_client_mods"
    mods_dir.mkdir(parents=True, exist_ok=True)
    disabled_dir.mkdir(parents=True, exist_ok=True)
    for mod_file in mod_files:
        shutil.copy2(mod_file, mods_dir / mod_file.name)
    (workspace / "README.txt").write_text("请根据 start.bat 或 start.sh 启动服务端。\n", encoding="utf-8")
    return workspace


def build_runnable_server_artifact(
    *,
    task_id: str,
    upload_archive: Path,
    workspace_root: Path,
    artifact_root: Path,
    analysis: ArchiveAnalysis,
    remote_fetcher: Callable[[RemoteModFile], bytes | RemoteFetchResult] | None = None,
) -> GeneratedServerArtifact:
    workspace_path = workspace_root / task_id
    archive_path = artifact_root / f"{task_id}-server.zip"

    if workspace_path.exists():
        shutil.rmtree(workspace_path)
    workspace_path.mkdir(parents=True, exist_ok=True)
    artifact_root.mkdir(parents=True, exist_ok=True)

    kept_mods = 0
    disabled_mods = 0
    copied_mod_names: set[str] = set()

    with zipfile.ZipFile(upload_archive) as archive:
        _assert_safe_archive(archive)

        for member in archive.infolist():
            if member.is_dir():
                continue
            member_path = PurePosixPath(member.filename)
            normalized = _strip_overrides_prefix(member_path)
            if normalized is None:
                continue

            if _is_mod_jar(normalized):
                decision, _, _ = decide_mod_side(normalized.name)
                target_dir = (
                    workspace_path / "_disabled_client_mods"
                    if decision == "disable_client_only"
                    else workspace_path / "mods"
                )
                target = target_dir / normalized.name
                _extract_member(archive, member, target)
                copied_mod_names.add(normalized.name)
                if decision == "disable_client_only":
                    disabled_mods += 1
                else:
                    kept_mods += 1
                continue

            if normalized.parts and normalized.parts[0].lower() in COPYABLE_DIRECTORIES:
                _extract_member(archive, member, workspace_path / Path(*normalized.parts))

    fetch_remote = remote_fetcher or _fetch_remote_mod_file
    for remote_file in analysis.remote_mod_files:
        remote_path = PurePosixPath(remote_file.path)
        _assert_safe_remote_mod_path(remote_path)
        if remote_path.name in copied_mod_names:
            continue

        fetched = fetch_remote(remote_file)
        if isinstance(fetched, RemoteFetchResult):
            content = fetched.content
            file_name = fetched.file_name or remote_path.name
        else:
            content = fetched
            file_name = remote_path.name
        _assert_safe_file_name(file_name)
        _verify_remote_mod_hash(remote_file, content)

        decision, _, _ = decide_mod_side(file_name)
        target_dir = (
            workspace_path / "_disabled_client_mods"
            if decision == "disable_client_only"
            else workspace_path / "mods"
        )
        target = target_dir / file_name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        copied_mod_names.add(file_name)

        if decision == "disable_client_only":
            disabled_mods += 1
        else:
            kept_mods += 1

    _write_runtime_files(workspace_path, analysis, kept_mods, disabled_mods)
    _zip_workspace(workspace_path, archive_path)

    return GeneratedServerArtifact(
        workspace_path=workspace_path,
        archive_path=archive_path,
        kept_mods=kept_mods,
        disabled_mods=disabled_mods,
    )


def write_verification_report(workspace_path: Path, result: VerificationResult) -> Path:
    report_path = workspace_path / "VERIFICATION.md"
    lines = [
        "# 启动验证报告",
        "",
        f"- 结果：{result.message}",
        "",
        "## 日志摘录",
    ]
    if result.log_excerpt:
        lines.extend(f"- `{line}`" for line in result.log_excerpt)
    else:
        lines.append("- 无日志输出")
    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def refresh_server_archive(artifact: GeneratedServerArtifact) -> None:
    _zip_workspace(artifact.workspace_path, artifact.archive_path)


def _assert_safe_archive(archive: zipfile.ZipFile) -> None:
    for member in archive.infolist():
        posix_path = PurePosixPath(member.filename)
        system_path = Path(member.filename)
        if (
            posix_path.is_absolute()
            or system_path.is_absolute()
            or ".." in posix_path.parts
            or ".." in system_path.parts
        ):
            raise ArchiveSecurityError("压缩包包含不安全路径")


def _strip_overrides_prefix(path: PurePosixPath) -> PurePosixPath | None:
    parts = path.parts
    if not parts:
        return None
    if parts[0].lower() in {"overrides", "client-overrides"}:
        parts = parts[1:]
    return PurePosixPath(*parts) if parts else None


def _is_mod_jar(path: PurePosixPath) -> bool:
    return (
        len(path.parts) >= 2
        and path.parts[0].lower() == "mods"
        and path.name.lower().endswith(".jar")
    )


def _assert_safe_remote_mod_path(path: PurePosixPath) -> None:
    if path.is_absolute() or ".." in path.parts or not _is_mod_jar(path):
        raise ArchiveSecurityError("整合包 manifest 包含不安全或不支持的远程 mod 路径")


def _assert_safe_file_name(file_name: str) -> None:
    path = PurePosixPath(file_name)
    if path.is_absolute() or ".." in path.parts or len(path.parts) != 1 or not file_name.lower().endswith(".jar"):
        raise ArchiveSecurityError("远程 mod 文件名不安全或不是 jar 文件")


def _fetch_remote_mod_file(remote_file: RemoteModFile) -> RemoteFetchResult:
    if remote_file.source == "curseforge":
        return _fetch_curseforge_mod_file(remote_file)

    if not remote_file.downloads:
        raise RemoteModDownloadError(f"{remote_file.path} 缺少下载地址")

    errors: list[str] = []
    for url in remote_file.downloads:
        try:
            response = httpx.get(url, follow_redirects=True, timeout=60.0)
            response.raise_for_status()
            return RemoteFetchResult(content=response.content)
        except httpx.HTTPError as exc:
            errors.append(f"{url}: {exc}")

    detail = "；".join(errors) if errors else "无可用下载地址"
    raise RemoteModDownloadError(f"无法下载 {remote_file.path}：{detail}")


def _fetch_curseforge_mod_file(remote_file: RemoteModFile) -> RemoteFetchResult:
    settings = get_settings()
    api_key = settings.curseforge_api_key
    if not api_key:
        raise RemoteModDownloadError(
            f"CurseForge manifest 文件 {remote_file.project_id}/{remote_file.file_id} 需要配置 CURSEFORGE_API_KEY"
        )
    if remote_file.project_id is None or remote_file.file_id is None:
        raise RemoteModDownloadError(f"{remote_file.path} 缺少 CurseForge projectID 或 fileID")

    headers = {"x-api-key": api_key, "Accept": "application/json"}
    with httpx.Client(base_url="https://api.curseforge.com", timeout=30.0, headers=headers) as client:
        file_response = client.get(
            f"/v1/mods/{remote_file.project_id}/files/{remote_file.file_id}"
        )
        file_response.raise_for_status()
        file_info = file_response.json().get("data", {})
        file_name = file_info.get("fileName") or f"{remote_file.project_id}-{remote_file.file_id}.jar"
        _assert_safe_file_name(file_name)

        download_url = file_info.get("downloadUrl")
        if not download_url:
            url_response = client.get(
                f"/v1/mods/{remote_file.project_id}/files/{remote_file.file_id}/download-url"
            )
            url_response.raise_for_status()
            download_url = url_response.json().get("data")

    if not isinstance(download_url, str) or not download_url:
        raise RemoteModDownloadError(
            f"CurseForge 文件 {remote_file.project_id}/{remote_file.file_id} 未提供可下载地址，可能未获得作者分发授权"
        )

    response = httpx.get(download_url, follow_redirects=True, timeout=60.0)
    response.raise_for_status()
    return RemoteFetchResult(content=response.content, file_name=file_name)


def _verify_remote_mod_hash(remote_file: RemoteModFile, content: bytes) -> None:
    for algorithm in ["sha512", "sha256", "sha1"]:
        expected = remote_file.hashes.get(algorithm)
        if not expected:
            continue
        actual = hashlib.new(algorithm, content).hexdigest()
        if actual.lower() != expected.lower():
            raise RemoteModDownloadError(
                f"{remote_file.path} 下载后 {algorithm} 校验失败"
            )
        return


def _extract_member(archive: zipfile.ZipFile, member: zipfile.ZipInfo, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with archive.open(member) as source, target.open("wb") as destination:
        shutil.copyfileobj(source, destination)


def _write_runtime_files(
    workspace_path: Path,
    analysis: ArchiveAnalysis,
    kept_mods: int,
    disabled_mods: int,
) -> None:
    (workspace_path / "eula.txt").write_text("eula=false\n", encoding="utf-8")
    (workspace_path / "start.bat").write_text(
        "\r\n".join(
            [
                "@echo off",
                "setlocal",
                "if not exist server.jar (",
                "  echo 未找到 server.jar，请先按 INSTALL.md 安装对应 Minecraft 服务端。",
                "  exit /b 1",
                ")",
                "java -Xms2G -Xmx4G -jar server.jar nogui",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (workspace_path / "start.sh").write_text(
        "\n".join(
            [
                "#!/usr/bin/env sh",
                "set -eu",
                'if [ ! -f "server.jar" ]; then',
                '  echo "未找到 server.jar，请先按 INSTALL.md 安装对应 Minecraft 服务端。"',
                "  exit 1",
                "fi",
                "java -Xms2G -Xmx4G -jar server.jar nogui",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (workspace_path / "INSTALL.md").write_text(
        _install_guide(analysis, kept_mods, disabled_mods),
        encoding="utf-8",
    )


def _install_guide(analysis: ArchiveAnalysis, kept_mods: int, disabled_mods: int) -> str:
    loader = analysis.loader or "未识别"
    minecraft_version = analysis.minecraft_version or "未识别"
    pack_name = analysis.pack_name or "未识别整合包"
    return "\n".join(
        [
            f"# {pack_name} 服务端",
            "",
            "## 当前产物",
            "",
            f"- Minecraft：{minecraft_version}",
            f"- Loader：{loader}",
            f"- 已放入 `mods/` 的 mod：{kept_mods}",
            f"- 已隔离到 `_disabled_client_mods/` 的客户端专用 mod：{disabled_mods}",
            "",
            "## 启动前步骤",
            "",
            "1. 安装与上面版本匹配的 Minecraft dedicated server 或对应 loader 服务端，并把启动 jar 命名为 `server.jar` 放到本目录。",
            "2. 阅读 Mojang EULA 后，将 `eula.txt` 中的 `eula=false` 改为 `eula=true`。",
            "3. Windows 运行 `start.bat`，Linux/macOS 运行 `sh start.sh`。",
            "",
            "## 说明",
            "",
            "本产物保留原始上传包不变，只复制服务端需要的文件到工作区。",
            "端侧判断证据不足的 mod 会先保留在 `mods/`，明显客户端专用的 mod 会进入 `_disabled_client_mods/`。",
            "如果启动失败，请优先查看日志中缺失依赖、loader 版本不匹配或客户端专用 mod 报错。",
            "",
        ]
    )


def _zip_workspace(workspace_path: Path, archive_path: Path) -> None:
    if archive_path.exists():
        archive_path.unlink()
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(workspace_path.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(workspace_path).as_posix())
