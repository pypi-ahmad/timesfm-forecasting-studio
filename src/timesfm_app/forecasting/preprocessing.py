from __future__ import annotations

import re

import numpy as np
import pandas as pd

from timesfm_app.contracts import DataQualityReport, PreparedSeries, SeriesSpec


class SeriesValidationError(ValueError):
    """Raised when tabular data cannot form one regular time series."""


def parse_manual_values(text: str) -> np.ndarray:
    tokens = [token.strip() for token in re.split(r"[,\r\n]+", text) if token.strip()]
    if len(tokens) < 2:
        raise ValueError("Enter at least two numeric values.")
    values: list[float] = []
    for position, token in enumerate(tokens, start=1):
        try:
            value = float(token)
        except ValueError as error:
            raise ValueError(f"Invalid number at position {position}.") from error
        if not np.isfinite(value):
            raise ValueError(f"Non-finite number at position {position}.")
        values.append(value)
    return np.asarray(values, dtype=np.float32)


def prepare_series(frame: pd.DataFrame, spec: SeriesSpec) -> PreparedSeries:
    missing_columns = {spec.date_column, spec.target_column} - set(frame.columns)
    if missing_columns:
        raise SeriesValidationError(f"Missing selected columns: {sorted(missing_columns)}")

    selected = frame[[spec.date_column, spec.target_column]].copy()
    selected[spec.date_column] = pd.to_datetime(selected[spec.date_column], errors="coerce")
    if selected[spec.date_column].isna().any():
        raise SeriesValidationError("Date column contains invalid or missing timestamps.")

    selected[spec.target_column] = pd.to_numeric(selected[spec.target_column], errors="coerce")
    selected = selected.sort_values(spec.date_column, kind="stable").reset_index(drop=True)
    if selected[spec.date_column].duplicated().any():
        raise SeriesValidationError("Date column contains duplicate timestamps.")

    timestamps = pd.DatetimeIndex(selected[spec.date_column])
    frequency = spec.frequency or _infer_frequency(timestamps)
    _validate_regular_timestamps(timestamps, frequency)

    values = selected[spec.target_column].to_numpy(dtype=np.float64)
    if np.isinf(values).any():
        raise SeriesValidationError("Target contains infinite values.")
    if not np.isfinite(values).any():
        raise SeriesValidationError("Target contains no finite values.")
    if np.isnan(values[-1]):
        raise SeriesValidationError(
            "Target has trailing missing values; forecast origin is ambiguous."
        )

    first_finite = int(np.flatnonzero(np.isfinite(values))[0])
    warnings: list[str] = []
    if first_finite:
        warnings.append(f"Trimmed {first_finite} leading missing target value(s).")
        values = values[first_finite:]
        timestamps = timestamps[first_finite:]

    values = values[-spec.context_length :].astype(np.float32, copy=False)
    timestamps = timestamps[-spec.context_length :]
    if len(values) < 2:
        raise SeriesValidationError("At least two usable observations are required.")
    if len(values) < 32:
        warnings.append("Context has fewer than 32 observations; forecast quality may be weak.")

    internal_missing = int(np.isnan(values[:-1]).sum())
    return PreparedSeries(
        timestamps=timestamps,
        values=values,
        frequency=frequency,
        report=DataQualityReport(
            source_rows=len(frame),
            usable_rows=len(values),
            internal_missing_values=internal_missing,
            warnings=tuple(warnings),
        ),
    )


def _infer_frequency(timestamps: pd.DatetimeIndex) -> str:
    try:
        frequency = pd.infer_freq(timestamps)
    except ValueError:
        frequency = None
    if frequency is None:
        raise SeriesValidationError(
            "Could not infer a regular frequency; select one manually and retry."
        )
    return frequency


def _validate_regular_timestamps(timestamps: pd.DatetimeIndex, frequency: str) -> None:
    try:
        expected = pd.date_range(start=timestamps[0], periods=len(timestamps), freq=frequency)
    except (TypeError, ValueError) as error:
        raise SeriesValidationError(f"Invalid frequency {frequency!r}.") from error
    if not timestamps.equals(expected):
        raise SeriesValidationError(
            f"Timestamps are not regular at frequency {frequency!r}; "
            "repair data before forecasting."
        )
