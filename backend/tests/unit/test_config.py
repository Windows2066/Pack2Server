from app.core.config import get_settings


def test_settings_accepts_common_curseforge_api_key_typo(monkeypatch):
    monkeypatch.delenv("CURSEFORGE_API_KEY", raising=False)
    monkeypatch.setenv("COUSEFORGE_API_KEY", "typo-key")
    get_settings.cache_clear()

    try:
        assert get_settings().curseforge_api_key == "typo-key"
    finally:
        get_settings.cache_clear()


def test_settings_reads_remote_mod_download_workers(monkeypatch):
    monkeypatch.setenv("REMOTE_MOD_DOWNLOAD_WORKERS", "12")
    get_settings.cache_clear()

    try:
        assert get_settings().remote_mod_download_workers == 12
    finally:
        get_settings.cache_clear()
