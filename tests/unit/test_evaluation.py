from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from timesfm_app.contracts import ForecastResult
from timesfm_app.evaluation import (
    anomaly_frame,
    build_rolling_origins,
    calculate_metrics,
    run_rolling_backtest,
)


def test_calculate_metrics_matches_hand_verified_point_and_probabilistic_values() -> None:
    actual = np.array([2.0, 4.0])
    point = np.array([1.0, 5.0])
    quantiles = {0.1: np.array([0.0, 3.0]), 0.9: np.array([3.0, 6.0])}

    metrics = calculate_metrics(
        actual, point, insample=np.array([0.0, 1.0, 2.0]), quantiles=quantiles
    )

    assert metrics["mae"] == pytest.approx(1.0)
    assert metrics["rmse"] == pytest.approx(1.0)
    assert metrics["bias"] == pytest.approx(0.0)
    assert metrics["smape"] == pytest.approx((2 / 3 + 2 / 9) / 2 * 100)
    assert metrics["wape"] == pytest.approx(100 / 3)
    assert metrics["mase"] == pytest.approx(1.0)
    assert metrics["rmsse"] == pytest.approx(1.0)
    assert metrics["coverage_10_90"] == pytest.approx(1.0)
    assert metrics["mean_interval_width_10_90"] == pytest.approx(3.0)
    assert metrics["mean_wql"] == pytest.approx(0.1)


def test_zero_denominators_are_reported_as_nan() -> None:
    metrics = calculate_metrics(np.zeros(2), np.ones(2), insample=np.zeros(3), quantiles={})
    assert np.isnan(metrics["wape"])
    assert np.isnan(metrics["mase"])
    assert np.isnan(metrics["rmsse"])


def test_rolling_origins_are_non_overlapping_and_respect_context() -> None:
    origins = build_rolling_origins(series_length=100, horizon=10, windows=3, min_context=32)
    assert origins == [(70, 80), (80, 90), (90, 100)]


def test_anomaly_frame_flags_values_outside_interval_with_normalized_severity() -> None:
    frame = anomaly_frame(
        pd.date_range("2025-01-01", periods=3, freq="D"),
        actual=np.array([0.0, 5.0, 12.0]),
        lower=np.array([0.0, 4.0, 8.0]),
        upper=np.array([2.0, 6.0, 10.0]),
    )
    assert frame["is_anomaly"].tolist() == [False, False, True]
    assert frame["severity"].tolist() == [0.0, 0.0, 1.0]


def test_run_rolling_backtest_returns_predictions_metrics_and_runtime() -> None:
    timestamps = pd.date_range("2025-01-01", periods=50, freq="D")
    values = np.arange(50, dtype=float)

    def forecast(context: np.ndarray, horizon: int) -> ForecastResult:
        point = np.repeat(context[-1] + 1, horizon)
        distribution = np.tile(np.arange(10, dtype=float), (horizon, 1)) + point[:, None] - 5
        return ForecastResult(None, point, distribution, "model", "revision", "cpu", 10)

    result = run_rolling_backtest(
        timestamps, values, horizon=5, windows=2, context_length=32, forecast=forecast
    )

    assert result.predictions["window"].nunique() == 2
    assert len(result.predictions) == 10
    assert {"mae", "rmse", "mean_wql", "latency_ms", "points_per_second"} <= set(
        result.metrics.columns
    )
    assert len(result.anomalies) == 10
