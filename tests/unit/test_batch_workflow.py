from __future__ import annotations

from pathlib import Path

import pandas as pd

from loader import LoadedDataset
from timesfm_app.contracts import ResolvedAsset
from timesfm_app.ui.controls import ForecastControls
from timesfm_app.ui.forecast_page import build_forecast_request


def test_each_dataset_can_use_its_own_column_mapping() -> None:
    asset = ResolvedAsset(Path("first.csv"), "upload", "first.csv", "a" * 64, 10)
    dataset = LoadedDataset(
        dataset_id="first",
        name="first.csv",
        asset=asset,
        frame=pd.DataFrame(
            {"when": pd.date_range("2026-01-01", periods=4), "demand": [1, 2, 3, 4]}
        ),
        datetime_columns=("when",),
    )
    controls = ForecastControls("cpu", context_length=3, horizon=2, frequency="D")

    request, prepared = build_forecast_request(
        dataset,
        date_column="when",
        target_column="demand",
        controls=controls,
        non_negative=True,
    )

    assert request.values.tolist() == [2, 3, 4]
    assert request.horizon == 2
    assert request.non_negative is True
    assert prepared.timestamps[0] == pd.Timestamp("2026-01-02")
