from app.core.config import get_settings


def test_settings_accepts_common_curseforge_api_key_typo(monkeypatch):
    monkeypatch.delenv("CURSEFORGE_API_KEY", raising=False)
    monkeypatch.setenv("COUSEFORGE_API_KEY", "typo-key")
    get_settings.cache_clear()

    try:
        assert get_settings().curseforge_api_key == "typo-key"
    finally:
        get_settings.cache_clear()
