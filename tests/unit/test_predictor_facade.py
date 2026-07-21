from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from predictor import DeviceSelectionError, TimesFMPredictor, resolve_device
from timesfm_app.config import AppSettings
from timesfm_app.contracts import ForecastRequest, ForecastResult


def test_resolve_device_supports_auto_cpu_and_cuda() -> None:
    assert resolve_device("auto", cuda_available=True) == "cuda"
    assert resolve_device("auto", cuda_available=False) == "cpu"
    assert resolve_device("cpu", cuda_available=True) == "cpu"
    assert resolve_device("cuda", cuda_available=True) == "cuda"


def test_resolve_device_rejects_unavailable_cuda() -> None:
    with pytest.raises(DeviceSelectionError, match="unavailable"):
        resolve_device("cuda", cuda_available=False)


def test_predictor_does_not_mutate_caller_settings() -> None:
    settings = AppSettings()

    predictor = TimesFMPredictor(settings, device="cpu")

    assert settings.device_preference == "auto"
    assert predictor.runtime.settings.device_preference == "cpu"


def test_predictor_returns_structured_dataframe() -> None:
    class FakeRuntime:
        def forecast(self, request: ForecastRequest) -> ForecastResult:
            distribution = np.tile(np.arange(10, dtype=np.float32), (request.horizon, 1))
            return ForecastResult(
                future_timestamps=pd.date_range("2026-01-01", periods=request.horizon),
                point=distribution[:, 5],
                distribution=distribution,
                model_id="model",
                model_revision="revision",
                device="cpu",
                latency_ms=1,
            )

    predictor = TimesFMPredictor(runtime=FakeRuntime())
    request = ForecastRequest(values=np.arange(10), context_length=10, horizon=2)

    output = predictor.predict(request, dataset_id="series")

    assert output.dataset_id == "series"
    assert output.frame.columns[-1] == "q90"
    assert output.frame.shape == (2, 13)


def test_predictor_retries_batch_members_to_isolate_failures() -> None:
    class PartiallyFailingRuntime:
        def forecast_many(self, requests: list[ForecastRequest]):
            raise RuntimeError("batch failed")

        def forecast(self, request: ForecastRequest) -> ForecastResult:
            if request.values[0] < 0:
                raise ValueError("bad series")
            distribution = np.zeros((request.horizon, 10), dtype=np.float32)
            return ForecastResult(
                None, distribution[:, 5], distribution, "model", "revision", "cpu", 1
            )

    predictor = TimesFMPredictor(runtime=PartiallyFailingRuntime())
    requests = {
        "good": ForecastRequest(np.arange(3), 3, 2),
        "bad": ForecastRequest(np.array([-1, 0, 1]), 3, 2),
    }

    output = predictor.predict_many(requests)

    assert set(output.forecasts) == {"good"}
    assert "bad series" in output.errors["bad"]
