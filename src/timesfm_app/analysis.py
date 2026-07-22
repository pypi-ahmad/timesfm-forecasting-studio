from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class EdaResult:
    summary: dict[str, float | int]
    trend: pd.DataFrame
    distribution: pd.DataFrame
    seasonal_profile: pd.DataFrame
    acf: pd.DataFrame
    outliers: pd.DataFrame
    decomposition: pd.DataFrame
    adf: dict[str, float] | None
    notes: tuple[str, ...]


def analyze_series(
    timestamps: pd.DatetimeIndex,
    values: np.ndarray,
    *,
    seasonal_period: int,
    max_diagnostic_rows: int = 50_000,
) -> EdaResult:
    series = pd.Series(np.asarray(values, dtype=float), index=timestamps, name="value")
    clean = series.dropna()
    notes: list[str] = []
    quantiles = clean.quantile([0.05, 0.25, 0.5, 0.75, 0.95]) if not clean.empty else pd.Series()
    mean = float(clean.mean()) if not clean.empty else np.nan
    std = float(clean.std(ddof=1)) if len(clean) > 1 else 0.0
    summary: dict[str, float | int] = {
        "count": len(series),
        "valid": int(clean.size),
        "missing": int(series.isna().sum()),
        "unique": int(clean.nunique()),
        "mean": mean,
        "std": std,
        "min": float(clean.min()) if not clean.empty else np.nan,
        "q05": float(quantiles.get(0.05, np.nan)),
        "q25": float(quantiles.get(0.25, np.nan)),
        "median": float(quantiles.get(0.5, np.nan)),
        "q75": float(quantiles.get(0.75, np.nan)),
        "q95": float(quantiles.get(0.95, np.nan)),
        "max": float(clean.max()) if not clean.empty else np.nan,
        "iqr": float(quantiles.get(0.75, np.nan) - quantiles.get(0.25, np.nan)),
        "skewness": float(clean.skew()) if len(clean) > 2 else np.nan,
        "kurtosis": float(clean.kurt()) if len(clean) > 3 else np.nan,
        "coefficient_of_variation": std / abs(mean) if mean and np.isfinite(mean) else np.nan,
    }

    rolling_window = max(2, min(seasonal_period, max(2, len(series) // 4)))
    trend = pd.DataFrame({"timestamp": timestamps, "value": series.to_numpy()})
    trend["rolling_mean"] = series.rolling(rolling_window, min_periods=2).mean().to_numpy()
    trend["rolling_std"] = series.rolling(rolling_window, min_periods=2).std().to_numpy()
    distribution = pd.DataFrame({"value": clean.to_numpy()})

    if seasonal_period > 1 and len(clean) >= seasonal_period:
        seasonal_profile = (
            pd.DataFrame(
                {
                    "seasonal_position": np.arange(len(series)) % seasonal_period,
                    "value": series.to_numpy(),
                }
            )
            .groupby("seasonal_position", as_index=False)["value"]
            .agg(["mean", "median", "count"])
        )
        seasonal_profile = seasonal_profile.reset_index()
    else:
        seasonal_profile = pd.DataFrame(columns=["seasonal_position", "mean", "median", "count"])
        notes.append("Seasonal diagnostics need at least one complete seasonal period.")

    constant = clean.nunique() <= 1
    if constant:
        notes.append(
            "The series is constant; lag, stationarity, and decomposition diagnostics are disabled."
        )
    diagnostic = clean.iloc[-max_diagnostic_rows:]
    max_lag = min(100, len(diagnostic) // 4)
    if not constant and max_lag >= 1:
        correlations = [1.0] + [float(diagnostic.autocorr(lag)) for lag in range(1, max_lag + 1)]
        confidence = 1.96 / np.sqrt(len(diagnostic))
        acf = pd.DataFrame(
            {
                "lag": range(max_lag + 1),
                "acf": correlations,
                "lower": -confidence,
                "upper": confidence,
            }
        )
    else:
        acf = pd.DataFrame(columns=["lag", "acf", "lower", "upper"])

    median = float(clean.median()) if not clean.empty else np.nan
    mad = float(np.median(np.abs(clean - median))) if not clean.empty else np.nan
    robust_z = np.zeros(len(series), dtype=float)
    if mad > 0:
        robust_z = 0.6745 * (series.fillna(median).to_numpy() - median) / mad
    outliers = pd.DataFrame(
        {
            "timestamp": timestamps,
            "value": series.to_numpy(),
            "robust_z": robust_z,
            "is_outlier": np.abs(robust_z) > 3.5,
        }
    )

    decomposition = pd.DataFrame()
    adf = None
    if not constant and len(diagnostic) >= max(2 * seasonal_period, 8):
        try:
            from statsmodels.tsa.seasonal import STL
            from statsmodels.tsa.stattools import adfuller

            fitted = STL(diagnostic, period=seasonal_period, robust=True).fit()
            decomposition = pd.DataFrame(
                {
                    "timestamp": diagnostic.index,
                    "observed": diagnostic.to_numpy(),
                    "trend": fitted.trend,
                    "seasonal": fitted.seasonal,
                    "residual": fitted.resid,
                }
            )
            statistic, pvalue, used_lag, observations, *_ = adfuller(diagnostic.to_numpy())
            adf = {
                "statistic": float(statistic),
                "pvalue": float(pvalue),
                "used_lag": float(used_lag),
                "observations": float(observations),
            }
        except (ImportError, ValueError, np.linalg.LinAlgError) as error:
            notes.append(f"STL/ADF diagnostics unavailable: {type(error).__name__}.")
    elif not constant:
        notes.append("STL/ADF diagnostics need at least two complete seasonal periods.")

    if len(clean) > max_diagnostic_rows:
        notes.append(f"Expensive diagnostics use the latest {max_diagnostic_rows:,} valid rows.")
    return EdaResult(
        summary=summary,
        trend=trend,
        distribution=distribution,
        seasonal_profile=seasonal_profile,
        acf=acf,
        outliers=outliers,
        decomposition=decomposition,
        adf=adf,
        notes=tuple(notes),
    )
