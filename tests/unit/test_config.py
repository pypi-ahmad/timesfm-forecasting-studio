from __future__ import annotations

from timesfm_app.config import AppSettings


def test_settings_accept_tokens_from_secret_mapping(monkeypatch) -> None:
    for name in ("HF_TOKEN", "KAGGLE_API_TOKEN", "KAGGLE_USERNAME", "KAGGLE_KEY"):
        monkeypatch.delenv(name, raising=False)

    settings = AppSettings.from_environment(
        secrets={"HF_TOKEN": "hf", "KAGGLE_API_TOKEN": "kaggle"}
    )

    assert settings.hf_token == "hf"
    assert settings.kaggle_api_token == "kaggle"
    assert "hf" not in repr(settings)
    assert "kaggle" not in repr(settings)
