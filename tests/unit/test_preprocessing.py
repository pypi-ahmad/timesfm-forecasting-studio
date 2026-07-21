from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from timesfm_app.contracts import ForecastRequest, SeriesSpec
from timesfm_app.forecasting.preprocessing import SeriesValidationError, prepare_series


def test_prepare_series_sorts_and_infers_daily_frequency() -> None:
    frame = pd.DataFrame({"when": ["2026-01-03", "2026-01-01", "2026-01-02"], "sales": [3, 1, 2]})

    prepared = prepare_series(frame, SeriesSpec("when", "sales", context_length=2))

    assert prepared.frequency == "D"
    np.testing.assert_array_equal(prepared.values, np.array([2, 3], dtype=np.float32))
    assert prepared.timestamps.tolist() == [pd.Timestamp("2026-01-02"), pd.Timestamp("2026-01-03")]


def test_prepare_series_rejects_duplicate_timestamps() -> None:
    frame = pd.DataFrame({"ds": ["2026-01-01", "2026-01-01"], "y": [1, 2]})

    with pytest.raises(SeriesValidationError, match="duplicate"):
        prepare_series(frame, SeriesSpec("ds", "y", context_length=2, frequency="D"))


def test_prepare_series_rejects_irregular_timestamps() -> None:
    frame = pd.DataFrame({"ds": ["2026-01-01", "2026-01-02", "2026-01-04"], "y": [1, 2, 4]})

    with pytest.raises(SeriesValidationError, match="regular"):
        prepare_series(frame, SeriesSpec("ds", "y", context_length=3, frequency="D"))


def test_prepare_series_trims_leading_nan_and_preserves_internal_nan() -> None:
    frame = pd.DataFrame(
        {
            "ds": pd.date_range("2026-01-01", periods=4, freq="D"),
            "y": [np.nan, 2.0, np.nan, 4.0],
        }
    )

    prepared = prepare_series(frame, SeriesSpec("ds", "y", context_length=4))

    assert prepared.values.shape == (3,)
    assert np.isnan(prepared.values[1])
    assert any("leading" in warning.lower() for warning in prepared.report.warnings)
    assert prepared.report.internal_missing_values == 1


def test_prepare_series_rejects_trailing_nan() -> None:
    frame = pd.DataFrame(
        {"ds": pd.date_range("2026-01-01", periods=3, freq="D"), "y": [1, 2, np.nan]}
    )

    with pytest.raises(SeriesValidationError, match="trailing"):
        prepare_series(frame, SeriesSpec("ds", "y", context_length=3))


def test_prepare_series_requires_manual_frequency_for_short_series() -> None:
    frame = pd.DataFrame({"ds": ["2026-01-01", "2026-01-02"], "y": [1, 2]})

    with pytest.raises(SeriesValidationError, match="frequency"):
        prepare_series(frame, SeriesSpec("ds", "y", context_length=2))


def test_forecast_request_calculates_compile_buckets() -> None:
    request = ForecastRequest(
        values=np.arange(35, dtype=np.float32), context_length=35, horizon=129
    )

    assert request.compile_context == 64
    assert request.compile_horizon == 256


def test_forecast_request_rejects_combined_limit() -> None:
    with pytest.raises(ValueError, match="16,384"):
        ForecastRequest(
            values=np.ones(15_361, dtype=np.float32), context_length=15_361, horizon=1_024
        )
