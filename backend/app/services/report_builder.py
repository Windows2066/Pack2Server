def build_success_report(
    *,
    pack_name: str,
    minecraft_version: str | None,
    loader: str | None,
    kept_mods: int,
    disabled_mods: int,
    verification_message: str | None = None,
    verification_logs: list[str] | None = None,
) -> str:
    lines = [
        "# 服务端生成完成",
        f"- 整合包：{pack_name}",
        f"- Minecraft：{minecraft_version or '未识别'}",
        f"- Loader：{loader or '未识别'}",
        f"- 保留服务端 mod：{kept_mods}",
        f"- 隔离客户端专用 mod：{disabled_mods}",
    ]
    if verification_message:
        lines.extend(["", "## 启动验证", f"- 结果：{verification_message}"])
        if verification_logs:
            lines.append("- 日志摘录：")
            lines.extend(f"  - `{line}`" for line in verification_logs[:10])
    return "\n".join(lines)


def build_failure_report(title: str, log_lines: list[str], next_step: str) -> str:
    lines = [f"# {title}", "", "## 关键日志"]
    lines.extend(f"- `{line}`" for line in log_lines[:20])
    lines.extend(["", f"下一步建议：{next_step}"])
    return "\n".join(lines)
