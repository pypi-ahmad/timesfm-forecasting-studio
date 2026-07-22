from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

DATASET_DEPENDENT_KEYS = (
    "forecast_outputs",
    "forecast_errors",
    "forecast_histories",
    "eda_result",
    "backtest_result",
    "anomaly_result",
    "report_bundle",
)


def clear_dataset_state(state: MutableMapping[str, Any]) -> None:
    """Clear session data while leaving the content-addressed disk cache intact."""
    state["loaded_assets"] = {}
    state["upload_generation"] = int(state.get("upload_generation", 0)) + 1
    for key in DATASET_DEPENDENT_KEYS:
        state.pop(key, None)
