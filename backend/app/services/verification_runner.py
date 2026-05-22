from dataclasses import dataclass


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    message: str
    log_excerpt: list[str]


def verify_startup(enabled: bool) -> VerificationResult:
    if not enabled:
        return VerificationResult(True, "启动验证已跳过", [])
    return VerificationResult(False, "启动验证尚未配置 Java 运行环境", ["Java runner not configured"])
