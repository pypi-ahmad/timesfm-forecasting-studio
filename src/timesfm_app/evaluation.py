from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd

from timesfm_app.contracts import ForecastResult


@dataclass(frozen=True)
class BacktestResult:
    predictions: pd.DataFrame
    metrics: pd.DataFrame
    anomalies: pd.DataFrame


def _safe_ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator > 0 and np.isfinite(denominator) else np.nan


def calculate_metrics(
    actual: np.ndarray,
    point: np.ndarray,
    *,
    insample: np.ndarray,
    quantiles: dict[float, np.ndarray],
) -> dict[str, float]:
    actual = np.asarray(actual, dtype=float)
    point = np.asarray(point, dtype=float)
    error = point - actual
    absolute = np.abs(error)
    squared = error**2
    denominator = np.abs(actual) + np.abs(point)
    scaled_absolute = np.abs(np.diff(np.asarray(insample, dtype=float)))
    scaled_squared = np.diff(np.asarray(insample, dtype=float)) ** 2
    metrics = {
        "mae": float(np.mean(absolute)),
        "rmse": float(np.sqrt(np.mean(squared))),
        "bias": float(np.mean(error)),
        "smape": float(
            np.mean(
                np.divide(
                    2 * absolute, denominator, out=np.zeros_like(absolute), where=denominator > 0
                )
            )
            * 100
        ),
        "wape": _safe_ratio(float(np.sum(absolute)) * 100, float(np.sum(np.abs(actual)))),
        "mase": _safe_ratio(float(np.mean(absolute)), float(np.mean(scaled_absolute))),
        "rmsse": np.sqrt(_safe_ratio(float(np.mean(squared)), float(np.mean(scaled_squared)))),
    }
    pinball: list[float] = []
    wql: list[float] = []
    actual_scale = float(np.sum(np.abs(actual)))
    for quantile, prediction in sorted(quantiles.items()):
        residual = actual - np.asarray(prediction, dtype=float)
        loss = np.maximum(quantile * residual, (quantile - 1) * residual)
        metrics[f"pinball_q{int(quantile * 100):02d}"] = float(np.mean(loss))
        pinball.append(float(np.mean(loss)))
        wql.append(_safe_ratio(2 * float(np.sum(loss)), actual_scale))
    metrics["mean_pinball"] = float(np.mean(pinball)) if pinball else np.nan
    metrics["mean_wql"] = float(np.nanmean(wql)) if wql else np.nan
    if 0.1 in quantiles and 0.9 in quantiles:
        lower = np.asarray(quantiles[0.1], dtype=float)
        upper = np.asarray(quantiles[0.9], dtype=float)
        width = upper - lower
        outside_low = actual < lower
        outside_high = actual > upper
        alpha = 0.2
        winkler = (
            width
            + (2 / alpha) * (lower - actual) * outside_low
            + (2 / alpha) * (actual - upper) * outside_high
        )
        metrics["coverage_10_90"] = float(np.mean((actual >= lower) & (actual <= upper)))
        metrics["mean_interval_width_10_90"] = float(np.mean(width))
        metrics["winkler_10_90"] = float(np.mean(winkler))
    return metrics


def build_rolling_origins(
    *, series_length: int, horizon: int, windows: int, min_context: int = 32
) -> list[tuple[int, int]]:
    if horizon < 1 or windows < 1:
        raise ValueError("Horizon and windows must be positive.")
    available = (series_length - min_context) // horizon
    count = min(windows, max(available, 0))
    if count == 0:
        raise ValueError("The series is too short for the requested rolling backtest.")
    first = series_length - count * horizon
    return [(first + index * horizon, first + (index + 1) * horizon) for index in range(count)]


def anomaly_frame(
    timestamps: pd.DatetimeIndex,
    *,
    actual: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
) -> pd.DataFrame:
    actual = np.asarray(actual, dtype=float)
    lower = np.asarray(lower, dtype=float)
    upper = np.asarray(upper, dtype=float)
    width = upper - lower
    distance = np.maximum(lower - actual, actual - upper)
    distance = np.maximum(distance, 0)
    severity = np.divide(distance, width, out=np.full_like(distance, np.inf), where=width > 0)
    severity[distance == 0] = 0
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "actual": actual,
            "lower": lower,
            "upper": upper,
            "is_anomaly": (actual < lower) | (actual > upper),
            "severity": severity,
        }
    )


def run_rolling_backtest(
    timestamps: pd.DatetimeIndex,
    values: np.ndarray,
    *,
    horizon: int,
    windows: int,
    context_length: int,
    forecast: Callable[[np.ndarray, int], ForecastResult],
    mode: str = "standard",
) -> BacktestResult:
    values = np.asarray(values, dtype=float)
    origins = build_rolling_origins(
        series_length=len(values),
        horizon=horizon,
        windows=windows,
        min_context=min(32, context_length),
    )
    predictions: list[pd.DataFrame] = []
    metric_rows: list[dict[str, float | int | str]] = []
    anomaly_rows: list[pd.DataFrame] = []
    for window, (origin, end) in enumerate(origins, start=1):
        context = values[max(0, origin - context_length) : origin]
        actual = values[origin:end]
        result = forecast(context, len(actual))
        quantiles = {
            quantile / 100: result.distribution[:, index]
            for index, quantile in enumerate(range(10, 100, 10), start=1)
        }
        metrics = calculate_metrics(actual, result.point, insample=context, quantiles=quantiles)
        metrics.update(
            {
                "window": window,
                "mode": mode,
                "latency_ms": result.latency_ms,
                "points_per_second": len(actual) / (result.latency_ms / 1_000)
                if result.latency_ms > 0
                else np.nan,
            }
        )
        metric_rows.append(metrics)
        prediction = pd.DataFrame(
            {
                "window": window,
                "mode": mode,
                "timestamp": timestamps[origin:end],
                "actual": actual,
                "point_q50": result.point,
            }
        )
        for index, quantile in enumerate(range(10, 100, 10), start=1):
            prediction[f"q{quantile}"] = result.distribution[:, index]
        predictions.append(prediction)
        anomalies = anomaly_frame(
            timestamps[origin:end], actual=actual, lower=quantiles[0.1], upper=quantiles[0.9]
        )
        anomalies.insert(0, "mode", mode)
        anomalies.insert(0, "window", window)
        anomaly_rows.append(anomalies)
    return BacktestResult(
        predictions=pd.concat(predictions, ignore_index=True),
        metrics=pd.DataFrame(metric_rows),
        anomalies=pd.concat(anomaly_rows, ignore_index=True),
    )
