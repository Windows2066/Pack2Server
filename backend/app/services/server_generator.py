import hashlib
import shutil
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Callable

import httpx

from app.core.config import get_settings
from app.services.archive_analyzer import ArchiveAnalysis, ArchiveSecurityError, RemoteModFile
from app.services.mod_decider import (
    ModSideDecision,
    PlatformModSideEvidence,
    decide_mod_side_detailed,
    modrinth_project_evidence,
    platform_identity_evidence,
)
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
    platform_evidence: list[PlatformModSideEvidence] = field(default_factory=list)


@dataclass(frozen=True)
class DownloadedRemoteMod:
    remote_file: RemoteModFile
    content: bytes
    file_name: str
    platform_evidence: list[PlatformModSideEvidence] = field(default_factory=list)


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
    remote_download_workers: int | None = None,
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
    mod_decisions: list[tuple[str, ModSideDecision]] = []
    temp_mod_dir = workspace_path / "_mod_decision_tmp"

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
                temp_target = temp_mod_dir / normalized.name
                _extract_member(archive, member, temp_target)
                decision = decide_mod_side_detailed(normalized.name, jar_path=temp_target)
                target = _target_for_mod_decision(workspace_path, normalized.name, decision)
                _move_file(temp_target, target)
                copied_mod_names.add(normalized.name)
                mod_decisions.append((normalized.name, decision))
                if decision.decision == "disable_client_only":
                    disabled_mods += 1
                else:
                    kept_mods += 1
                continue

            if normalized.parts and normalized.parts[0].lower() in COPYABLE_DIRECTORIES:
                _extract_member(archive, member, workspace_path / Path(*normalized.parts))

    fetch_remote = remote_fetcher or _fetch_remote_mod_file
    downloaded_remote_mods = _download_remote_mods(
        analysis.remote_mod_files,
        copied_mod_names,
        fetch_remote,
        remote_download_workers or get_settings().remote_mod_download_workers,
    )
    for downloaded in downloaded_remote_mods:
        content = downloaded.content
        file_name = downloaded.file_name
        if file_name in copied_mod_names:
            continue

        temp_target = temp_mod_dir / file_name
        temp_target.parent.mkdir(parents=True, exist_ok=True)
        temp_target.write_bytes(content)
        decision = decide_mod_side_detailed(
            file_name,
            jar_path=temp_target,
            platform_evidence=downloaded.platform_evidence,
        )
        target = _target_for_mod_decision(workspace_path, file_name, decision)
        _move_file(temp_target, target)
        copied_mod_names.add(file_name)
        mod_decisions.append((file_name, decision))

        if decision.decision == "disable_client_only":
            disabled_mods += 1
        else:
            kept_mods += 1

    if temp_mod_dir.exists():
        shutil.rmtree(temp_mod_dir)
    _write_runtime_files(workspace_path, analysis, kept_mods, disabled_mods)
    _write_mod_decision_report(workspace_path, mod_decisions)
    _zip_workspace(workspace_path, archive_path)

    return GeneratedServerArtifact(
        workspace_path=workspace_path,
        archive_path=archive_path,
        kept_mods=kept_mods,
        disabled_mods=disabled_mods,
    )


def _download_remote_mods(
    remote_files: list[RemoteModFile],
    copied_mod_names: set[str],
    fetch_remote: Callable[[RemoteModFile], bytes | RemoteFetchResult],
    worker_count: int,
) -> list[DownloadedRemoteMod]:
    pending_remote_files: list[RemoteModFile] = []
    for remote_file in remote_files:
        remote_path = PurePosixPath(remote_file.path)
        _assert_safe_remote_mod_path(remote_path)
        if remote_path.name in copied_mod_names:
            continue
        pending_remote_files.append(remote_file)

    if not pending_remote_files:
        return []

    workers = max(1, worker_count)
    if workers == 1 or len(pending_remote_files) == 1:
        return [
            _download_one_remote_mod(remote_file, fetch_remote)
            for remote_file in pending_remote_files
        ]

    with ThreadPoolExecutor(max_workers=min(workers, len(pending_remote_files))) as executor:
        return list(executor.map(lambda item: _download_one_remote_mod(item, fetch_remote), pending_remote_files))


def _download_one_remote_mod(
    remote_file: RemoteModFile,
    fetch_remote: Callable[[RemoteModFile], bytes | RemoteFetchResult],
) -> DownloadedRemoteMod:
    remote_path = PurePosixPath(remote_file.path)
    _assert_safe_remote_mod_path(remote_path)

    fetched = fetch_remote(remote_file)
    if isinstance(fetched, RemoteFetchResult):
        content = fetched.content
        file_name = fetched.file_name or remote_path.name
    else:
        content = fetched
        file_name = remote_path.name
    _assert_safe_file_name(file_name)
    _verify_remote_mod_hash(remote_file, content)

    return DownloadedRemoteMod(
        remote_file=remote_file,
        content=content,
        file_name=file_name,
        platform_evidence=fetched.platform_evidence if isinstance(fetched, RemoteFetchResult) else [],
    )


def _target_for_mod_decision(
    workspace_path: Path,
    file_name: str,
    decision: ModSideDecision,
) -> Path:
    target_dir = (
        workspace_path / "_disabled_client_mods"
        if decision.decision == "disable_client_only"
        else workspace_path / "mods"
    )
    return target_dir / file_name


def _move_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    shutil.move(str(source), str(target))


def _write_mod_decision_report(
    workspace_path: Path,
    decisions: list[tuple[str, ModSideDecision]],
) -> Path:
    report_path = workspace_path / "MOD_DECISIONS.md"
    lines = [
        "# mod 端侧判定报告",
        "",
        "| 文件 | 决策 | 置信度 | 证据来源 | 说明 |",
        "| --- | --- | ---: | --- | --- |",
    ]
    if not decisions:
        lines.append("| 无 | keep_unknown | 0 | unknown | 未发现 mod 文件 |")
    else:
        for filename, decision in decisions:
            lines.append(
                f"| `{filename}` | `{decision.decision}` | {decision.confidence:.2f} | "
                f"`{decision.evidence_source}` | {decision.reason} |"
            )
    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


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
            return RemoteFetchResult(
                content=response.content,
                platform_evidence=_fetch_modrinth_platform_evidence(remote_file),
            )
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

        mod_info = _fetch_curseforge_mod_info(client, remote_file)

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
    evidence = _curseforge_platform_evidence(file_name, mod_info)
    return RemoteFetchResult(
        content=response.content,
        file_name=file_name,
        platform_evidence=[evidence] if evidence else [],
    )


def _fetch_modrinth_platform_evidence(remote_file: RemoteModFile) -> list[PlatformModSideEvidence]:
    if remote_file.source != "modrinth" or not remote_file.project_id:
        return []
    try:
        response = httpx.get(
            f"https://api.modrinth.com/v2/project/{remote_file.project_id}",
            headers={"User-Agent": "opc-mc-server-pack-builder/0.1"},
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return []
    evidence = modrinth_project_evidence(response.json())
    return [evidence] if evidence else []


def _curseforge_platform_evidence(
    file_name: str,
    mod_info: dict,
) -> PlatformModSideEvidence | None:
    return platform_identity_evidence(
        source="curseforge_metadata",
        identifiers=[
            file_name,
            _string_or_none(mod_info.get("slug")),
            _string_or_none(mod_info.get("name")),
            _string_or_none(mod_info.get("summary")),
        ],
        reason_prefix="CurseForge 项目元数据",
    )


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _fetch_curseforge_mod_info(client: httpx.Client, remote_file: RemoteModFile) -> dict:
    try:
        response = client.get(f"/v1/mods/{remote_file.project_id}")
        response.raise_for_status()
    except httpx.HTTPError:
        return {}
    data = response.json().get("data", {})
    return data if isinstance(data, dict) else {}


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
