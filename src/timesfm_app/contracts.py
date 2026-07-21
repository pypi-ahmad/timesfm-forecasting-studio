from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from math import ceil
from pathlib import Path

import numpy as np
import pandas as pd

TIMESFM_CONTEXT_LIMIT = 16_384
INPUT_PATCH_LENGTH = 32
OUTPUT_PATCH_LENGTH = 128
MAX_QUANTILE_HORIZON = 1_024
SUPPORTED_SUFFIXES = frozenset({".csv", ".parquet", ".xlsx"})


@dataclass(frozen=True)
class ResolvedAsset:
    path: Path
    source_kind: str
    locator: str
    sha256: str
    size_bytes: int
    retrieved_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    revision: str | None = None


@dataclass(frozen=True)
class SeriesSpec:
    date_column: str
    target_column: str
    context_length: int
    frequency: str | None = None

    def __post_init__(self) -> None:
        if self.context_length < 2:
            raise ValueError("Context length must be at least 2.")


@dataclass(frozen=True)
class DataQualityReport:
    source_rows: int
    usable_rows: int
    internal_missing_values: int = 0
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class PreparedSeries:
    timestamps: pd.DatetimeIndex
    values: np.ndarray
    frequency: str
    report: DataQualityReport


@dataclass(frozen=True)
class ForecastRequest:
    values: np.ndarray
    context_length: int
    horizon: int
    timestamps: pd.DatetimeIndex | None = None
    frequency: str | None = None
    non_negative: bool = False
    compile_context: int = field(init=False)
    compile_horizon: int = field(init=False)

    def __post_init__(self) -> None:
        values = np.asarray(self.values, dtype=np.float32)
        if values.ndim != 1:
            raise ValueError("Forecast values must be one-dimensional.")
        if self.context_length < 2:
            raise ValueError("Context length must be at least 2.")
        if self.horizon < 1 or self.horizon > MAX_QUANTILE_HORIZON:
            raise ValueError(f"Horizon must be between 1 and {MAX_QUANTILE_HORIZON:,}.")

        compile_context = ceil(self.context_length / INPUT_PATCH_LENGTH) * INPUT_PATCH_LENGTH
        compile_horizon = ceil(self.horizon / OUTPUT_PATCH_LENGTH) * OUTPUT_PATCH_LENGTH
        if compile_context + compile_horizon > TIMESFM_CONTEXT_LIMIT:
            raise ValueError("Rounded context plus horizon exceeds TimesFM limit of 16,384 points.")

        object.__setattr__(self, "values", values[-self.context_length :])
        object.__setattr__(self, "compile_context", compile_context)
        object.__setattr__(self, "compile_horizon", compile_horizon)


@dataclass(frozen=True)
class ForecastResult:
    future_timestamps: pd.DatetimeIndex | None
    point: np.ndarray
    distribution: np.ndarray
    model_id: str
    model_revision: str
    device: str
    latency_ms: float
    warnings: tuple[str, ...] = ()
