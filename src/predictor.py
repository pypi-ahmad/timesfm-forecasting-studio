"""Pandas-oriented TimesFM predictor facade."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

import pandas as pd

from timesfm_app.config import AppSettings
from timesfm_app.contracts import ForecastRequest, ForecastResult
from timesfm_app.forecasting.runtime import TimesFMRuntime
from timesfm_app.ui.results import forecast_frame

DeviceChoice = Literal["auto", "cpu", "cuda"]


class DeviceSelectionError(ValueError):
    """Raised when a requested compute device cannot be used."""


@dataclass(frozen=True)
class PredictionOutput:
    dataset_id: str
    result: ForecastResult
    frame: pd.DataFrame


@dataclass(frozen=True)
class BatchPrediction:
    forecasts: dict[str, PredictionOutput]
    errors: dict[str, str]


def resolve_device(preference: DeviceChoice, *, cuda_available: bool | None = None) -> str:
    if preference == "cpu":
        return "cpu"
    if preference not in {"auto", "cuda"}:
        raise DeviceSelectionError(f"Unsupported compute device: {preference!r}.")
    if cuda_available is None:
        import torch

        cuda_available = torch.cuda.is_available()
    if preference == "cuda" and not cuda_available:
        raise DeviceSelectionError("CUDA was requested but is unavailable.")
    if preference == "auto":
        return "cuda" if cuda_available else "cpu"
    return "cuda"


class TimesFMPredictor:
    def __init__(
        self,
        settings: AppSettings | None = None,
        *,
        device: DeviceChoice = "auto",
        runtime: TimesFMRuntime | None = None,
    ) -> None:
        if runtime is not None:
            self.runtime = runtime
            return
        active_settings = settings or AppSettings.from_environment()
        active_settings = replace(active_settings, device_preference=resolve_device(device))
        self.runtime = TimesFMRuntime(active_settings)

    def predict(self, request: ForecastRequest, *, dataset_id: str = "series") -> PredictionOutput:
        result = self.runtime.forecast(request)
        return PredictionOutput(dataset_id, result, forecast_frame(result))

    def predict_many(self, requests: dict[str, ForecastRequest]) -> BatchPrediction:
        forecasts: dict[str, PredictionOutput] = {}
        errors: dict[str, str] = {}
        groups: dict[tuple[int, bool], list[tuple[str, ForecastRequest]]] = {}
        for dataset_id, request in requests.items():
            groups.setdefault((request.horizon, request.non_negative), []).append(
                (dataset_id, request)
            )
        for members in groups.values():
            try:
                results = self.runtime.forecast_many([request for _, request in members])
                for (dataset_id, _request), result in zip(members, results, strict=True):
                    forecasts[dataset_id] = PredictionOutput(
                        dataset_id, result, forecast_frame(result)
                    )
            except Exception:
                self._retry_individually(members, forecasts, errors)
        return BatchPrediction(forecasts, errors)

    def _retry_individually(
        self,
        members: list[tuple[str, ForecastRequest]],
        forecasts: dict[str, PredictionOutput],
        errors: dict[str, str],
    ) -> None:
        for dataset_id, request in members:
            try:
                forecasts[dataset_id] = self.predict(request, dataset_id=dataset_id)
            except Exception as error:
                errors[dataset_id] = f"{type(error).__name__}: {error}"
