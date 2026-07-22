from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from timesfm_app.config import AppSettings
from timesfm_app.contracts import CovariateForecastRequest
from timesfm_app.forecasting.runtime import TimesFMRuntime


class FakeXRegModel:
    def __init__(self) -> None:
        self.model = type("Inner", (), {"device": "cpu"})()
        self.compile_calls: list[object] = []
        self.calls: list[dict[str, object]] = []

    def compile(self, config: object) -> None:
        self.compile_calls.append(config)

    def forecast_with_covariates(self, **kwargs: object):
        self.calls.append(kwargs)
        horizon = len(next(iter(kwargs["dynamic_numerical_covariates"].values()))[0]) - len(
            kwargs["inputs"][0]
        )
        point = [np.arange(horizon, dtype=np.float32)]
        distribution = [np.tile(np.arange(10, dtype=np.float32), (horizon, 1))]
        return point, distribution


def test_covariate_request_requires_future_dynamic_values() -> None:
    with pytest.raises(ValueError, match="context plus horizon"):
        CovariateForecastRequest(
            values=np.arange(10),
            horizon=2,
            dynamic_numerical={"temperature": np.arange(11)},
        )


def test_runtime_forecasts_with_covariates_and_forces_xreg_cpu(workspace_tmp_path: Path) -> None:
    model = FakeXRegModel()

    class Config:
        def __init__(self, **kwargs: object) -> None:
            self.__dict__.update(kwargs)

    runtime = TimesFMRuntime(
        AppSettings(cache_root=workspace_tmp_path),
        model_loader=lambda *_args, **_kwargs: model,
        config_factory=Config,
    )
    request = CovariateForecastRequest(
        values=np.arange(10),
        horizon=2,
        timestamps=pd.date_range("2025-01-01", periods=10, freq="D"),
        frequency="D",
        dynamic_numerical={"temperature": np.arange(12)},
        dynamic_categorical={"promotion": ["no"] * 10 + ["yes", "yes"]},
        mode="timesfm + xreg",
    )

    result = runtime.forecast_with_covariates(request)

    assert model.compile_calls[0].return_backcast is True
    assert model.calls[0]["force_on_cpu"] is True
    assert model.calls[0]["xreg_mode"] == "timesfm + xreg"
    assert model.calls[0]["dynamic_categorical_covariates"]["promotion"][0] == [0] * 10 + [1, 1]
    assert result.point.tolist() == [0, 1]
    assert result.future_timestamps[-1] == pd.Timestamp("2025-01-12")
