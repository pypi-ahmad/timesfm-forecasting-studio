from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AppSettings:
    cache_root: Path = Path(".cache")
    model_id: str = "google/timesfm-2.5-200m-pytorch"
    model_revision: str = "1d952420fba87f3c6dee4f240de0f1a0fbc790e3"
    offline: bool = False
    hf_token: str | None = field(default=None, repr=False)
    kaggle_api_token: str | None = field(default=None, repr=False)
    kaggle_username: str | None = field(default=None, repr=False)
    kaggle_key: str | None = field(default=None, repr=False)
    max_context_length: int = 16_256
    device_preference: str = "auto"

    @property
    def model_cache(self) -> Path:
        return self.cache_root / "huggingface"

    @property
    def data_cache(self) -> Path:
        return self.cache_root / "data"

    @classmethod
    def from_environment(cls, *, secrets: dict[str, object] | None = None) -> AppSettings:
        secret_values = secrets or {}
        cache_root = Path(
            os.getenv("TIMESFM_APP_CACHE", str(secret_values.get("TIMESFM_APP_CACHE", ".cache")))
        )
        token = os.getenv("HF_TOKEN") or _optional_string(secret_values.get("HF_TOKEN"))
        kaggle_api_token = os.getenv("KAGGLE_API_TOKEN") or _optional_string(
            secret_values.get("KAGGLE_API_TOKEN")
        )
        kaggle_username = os.getenv("KAGGLE_USERNAME") or _optional_string(
            secret_values.get("KAGGLE_USERNAME")
        )
        kaggle_key = os.getenv("KAGGLE_KEY") or _optional_string(secret_values.get("KAGGLE_KEY"))
        offline_text = os.getenv(
            "TIMESFM_OFFLINE", str(secret_values.get("TIMESFM_OFFLINE", "false"))
        )
        return cls(
            cache_root=cache_root,
            offline=offline_text.lower() in {"1", "true", "yes"},
            hf_token=token,
            kaggle_api_token=kaggle_api_token,
            kaggle_username=kaggle_username,
            kaggle_key=kaggle_key,
        )


def _optional_string(value: object) -> str | None:
    return str(value) if value not in {None, ""} else None
