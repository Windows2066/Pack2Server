from app.services.report_builder import build_failure_report, build_success_report


def test_build_success_report_uses_chinese_summary():
    report = build_success_report(
        pack_name="测试整合包",
        minecraft_version="1.20.1",
        loader="forge",
        kept_mods=2,
        disabled_mods=1,
    )

    assert "服务端生成完成" in report
    assert "测试整合包" in report
    assert "隔离客户端专用 mod：1" in report


def test_build_failure_report_includes_next_step():
    report = build_failure_report("启动验证失败", ["Missing dependency"], "请检查前置依赖")

    assert "启动验证失败" in report
    assert "Missing dependency" in report
    assert "下一步建议：请检查前置依赖" in report
