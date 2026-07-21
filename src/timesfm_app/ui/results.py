from __future__ import annotations

import pandas as pd

from timesfm_app.contracts import ForecastResult


def forecast_frame(result: ForecastResult) -> pd.DataFrame:
    horizon = len(result.point)
    timestamps = (
        result.future_timestamps
        if result.future_timestamps is not None
        else pd.Series([pd.NaT] * horizon, dtype="datetime64[ns]")
    )
    data: dict[str, object] = {
        "step": range(1, horizon + 1),
        "timestamp": timestamps,
        "point_q50": result.point,
        "mean": result.distribution[:, 0],
    }
    for index, quantile in enumerate(range(10, 100, 10), start=1):
        data[f"q{quantile}"] = result.distribution[:, index]
    return pd.DataFrame(data)
