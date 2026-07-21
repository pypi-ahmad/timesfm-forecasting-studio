from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from timesfm_app.config import AppSettings
from timesfm_app.contracts import ForecastRequest, ForecastResult
from timesfm_app.forecasting.preprocessing import parse_manual_values
from timesfm_app.forecasting.runtime import ForecastRuntimeError, TimesFMRuntime, build_future_index
from timesfm_app.ui.charts import build_forecast_chart
from timesfm_app.ui.results import forecast_frame


@dataclass
class FakeConfig:
    max_context: int
    max_horizon: int
    normalize_inputs: bool
    per_core_batch_size: int
    use_continuous_quantile_head: bool
    force_flip_invariance: bool
    infer_is_positive: bool
    fix_quantile_crossing: bool


class FakeModel:
    def __init__(self) -> None:
        self.compile_calls: list[FakeConfig] = []
        self.model = type("InnerModel", (), {"device": "cuda:0"})()

    def compile(self, config: FakeConfig) -> None:
        self.compile_calls.append(config)

    def forecast(self, *, horizon: int, inputs: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
        distribution = np.zeros((len(inputs), horizon, 10), dtype=np.float32)
        distribution[:, :, 0] = 10
        for index in range(1, 10):
            distribution[:, :, index] = index
        return distribution[:, :, 5], distribution


def test_runtime_loads_once_compiles_and_returns_dated_forecast(workspace_tmp_path: Path) -> None:
    model = FakeModel()
    load_calls: list[dict[str, object]] = []

    def loader(*_args: object, **kwargs: object) -> FakeModel:
        load_calls.append(kwargs)
        return model

    settings = AppSettings(cache_root=workspace_tmp_path, hf_token="hidden")
    runtime = TimesFMRuntime(
        settings,
        model_loader=loader,
        config_factory=FakeConfig,
    )
    request = ForecastRequest(
        values=np.arange(35, dtype=np.float32),
        context_length=35,
        horizon=3,
        timestamps=pd.date_range("2026-01-01", periods=35, freq="D"),
        frequency="D",
    )

    first = runtime.forecast(request)
    second = runtime.forecast(request)

    assert len(load_calls) == 1
    assert load_calls[0]["token"] == "hidden"
    assert len(model.compile_calls) == 1
    assert model.compile_calls[0].max_context == 64
    assert model.compile_calls[0].max_horizon == 128
    assert first.future_timestamps.tolist() == list(
        pd.date_range("2026-02-05", periods=3, freq="D")
    )
    np.testing.assert_array_equal(first.point, np.array([5, 5, 5], dtype=np.float32))
    assert first.device == "cuda:0"
    assert second.model_revision == settings.model_revision


def test_runtime_maps_non_negative_flag_into_config(workspace_tmp_path: Path) -> None:
    model = FakeModel()
    runtime = TimesFMRuntime(
        AppSettings(cache_root=workspace_tmp_path),
        model_loader=lambda *_args, **_kwargs: model,
        config_factory=FakeConfig,
    )

    runtime.forecast(
        ForecastRequest(
            values=np.arange(10, dtype=np.float32),
            context_length=10,
            horizon=2,
            non_negative=True,
        )
    )

    assert model.compile_calls[0].infer_is_positive is True


def test_runtime_forecasts_variable_length_series_as_one_batch(workspace_tmp_path: Path) -> None:
    model = FakeModel()
    runtime = TimesFMRuntime(
        AppSettings(cache_root=workspace_tmp_path),
        model_loader=lambda *_args, **_kwargs: model,
        config_factory=FakeConfig,
    )
    requests = [
        ForecastRequest(values=np.arange(35), context_length=35, horizon=3),
        ForecastRequest(values=np.arange(60), context_length=60, horizon=3),
    ]

    results = runtime.forecast_many(requests)

    assert len(results) == 2
    assert results[0].point.shape == (3,)
    assert model.compile_calls[0].max_context == 64


def test_runtime_rejects_invalid_output_shape(workspace_tmp_path: Path) -> None:
    class BadModel(FakeModel):
        def forecast(self, **_kwargs: object) -> tuple[np.ndarray, np.ndarray]:
            return np.zeros((1, 2)), np.zeros((1, 2, 9))

    runtime = TimesFMRuntime(
        AppSettings(cache_root=workspace_tmp_path),
        model_loader=lambda *_args, **_kwargs: BadModel(),
        config_factory=FakeConfig,
    )

    with pytest.raises(ForecastRuntimeError, match="distribution"):
        runtime.forecast(ForecastRequest(values=np.arange(10), context_length=10, horizon=2))


def test_build_future_index_preserves_month_end_frequency() -> None:
    future = build_future_index(pd.Timestamp("2026-01-31"), "ME", 3)

    assert future.tolist() == [
        pd.Timestamp("2026-02-28"),
        pd.Timestamp("2026-03-31"),
        pd.Timestamp("2026-04-30"),
    ]


def test_parse_manual_values_supports_commas_and_newlines() -> None:
    values = parse_manual_values("10, 12\n15,14, 18")

    np.testing.assert_array_equal(values, np.array([10, 12, 15, 14, 18], dtype=np.float32))


def test_parse_manual_values_reports_bad_token_position() -> None:
    with pytest.raises(ValueError, match="position 3"):
        parse_manual_values("10, 12, nope")


def test_build_forecast_chart_contains_history_point_and_interval() -> None:
    timestamps = pd.date_range("2026-01-01", periods=3, freq="D")
    distribution = np.zeros((2, 10), dtype=np.float32)
    distribution[:, 1] = [2, 3]
    distribution[:, 5] = [5, 6]
    distribution[:, 9] = [8, 9]
    result = ForecastResult(
        future_timestamps=pd.date_range("2026-01-04", periods=2, freq="D"),
        point=np.array([5, 6], dtype=np.float32),
        distribution=distribution,
        model_id="model",
        model_revision="revision",
        device="cpu",
        latency_ms=1,
    )

    figure = build_forecast_chart(timestamps, np.array([1, 2, 3]), result)

    assert [trace.name for trace in figure.data] == ["History", "q10", "q90", "Forecast (q50)"]
    assert figure.data[2].fill == "tonexty"


def test_forecast_frame_maps_mean_and_quantile_channels() -> None:
    distribution = np.tile(np.arange(10, dtype=np.float32), (2, 1))
    result = ForecastResult(
        future_timestamps=pd.date_range("2026-01-01", periods=2, freq="D"),
        point=np.array([5, 5], dtype=np.float32),
        distribution=distribution,
        model_id="model",
        model_revision="revision",
        device="cpu",
        latency_ms=1,
    )

    frame = forecast_frame(result)

    assert frame.columns.tolist() == [
        "step",
        "timestamp",
        "point_q50",
        "mean",
        "q10",
        "q20",
        "q30",
        "q40",
        "q50",
        "q60",
        "q70",
        "q80",
        "q90",
    ]
    assert frame.loc[0, "mean"] == 0
    assert frame.loc[0, "q90"] == 9
