from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from timesfm_app.analysis import analyze_series


def test_analyze_series_produces_quality_distribution_trend_and_lag_diagnostics() -> None:
    timestamps = pd.date_range("2025-01-01", periods=120, freq="D")
    values = np.sin(np.arange(120) * 2 * np.pi / 7) + np.arange(120) / 100

    result = analyze_series(timestamps, values, seasonal_period=7)

    assert result.summary["count"] == 120
    assert result.summary["missing"] == 0
    assert result.summary["skewness"] == pytest.approx(pd.Series(values).skew())
    assert {"timestamp", "value", "rolling_mean", "rolling_std"} <= set(result.trend)
    assert result.seasonal_profile.shape[0] == 7
    assert result.acf.loc[result.acf["lag"] == 0, "acf"].iat[0] == pytest.approx(1.0)
    assert result.outliers["is_outlier"].dtype == bool
    assert result.notes == ()


def test_analyze_series_handles_missing_and_constant_short_series() -> None:
    timestamps = pd.date_range("2025-01-01", periods=4, freq="h")
    result = analyze_series(timestamps, np.array([2.0, np.nan, 2.0, 2.0]), seasonal_period=24)

    assert result.summary["missing"] == 1
    assert result.summary["std"] == 0
    assert result.acf.empty
    assert any("constant" in note.lower() for note in result.notes)
    assert any("seasonal" in note.lower() for note in result.notes)
