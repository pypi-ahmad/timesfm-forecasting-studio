from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd

from timesfm_app.config import AppSettings
from timesfm_app.contracts import CovariateForecastRequest, ForecastRequest, ForecastResult

logger = logging.getLogger(__name__)


class ForecastRuntimeError(RuntimeError):
    """Raised when TimesFM cannot produce a valid forecast contract."""


class TimesFMRuntime:
    def __init__(
        self,
        settings: AppSettings,
        *,
        model_loader: Callable[..., Any] | None = None,
        config_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.settings = settings
        self._model_loader = model_loader
        self._config_factory = config_factory
        self._model: Any | None = None
        self._compile_key: tuple[int, int, bool] | None = None
        self._lock = threading.RLock()

    def forecast(self, request: ForecastRequest) -> ForecastResult:
        return self.forecast_many([request])[0]

    def forecast_many(self, requests: list[ForecastRequest]) -> list[ForecastResult]:
        if not requests:
            return []
        horizons = {request.horizon for request in requests}
        positivity = {request.non_negative for request in requests}
        if len(horizons) != 1 or len(positivity) != 1:
            raise ForecastRuntimeError(
                "A TimesFM batch must share one horizon and non-negative setting."
            )
        started = time.perf_counter()
        horizon = requests[0].horizon
        compile_context = max(request.compile_context for request in requests)
        with self._lock:
            model = self._get_model()
            compile_key = (
                compile_context,
                requests[0].compile_horizon,
                requests[0].non_negative,
            )
            if compile_key != self._compile_key:
                model.compile(self._make_config(requests[0], max_context=compile_context))
                self._compile_key = compile_key
            # TimesFM expects one 1-D float array per series. It returns a batch-major
            # point matrix and a final channel dimension of mean, then q10 through q90.
            point, distribution = model.forecast(
                horizon=horizon,
                inputs=[request.values for request in requests],
            )

        point_array = np.asarray(point, dtype=np.float32)
        distribution_array = np.asarray(distribution, dtype=np.float32)
        expected_point = (len(requests), horizon)
        expected_distribution = (len(requests), horizon, 10)
        if point_array.shape != expected_point:
            raise ForecastRuntimeError(
                f"TimesFM returned invalid point shape {point_array.shape}; "
                f"expected {expected_point}."
            )
        if distribution_array.shape != expected_distribution:
            raise ForecastRuntimeError(
                "TimesFM returned invalid distribution shape "
                f"{distribution_array.shape}; expected {expected_distribution}."
            )
        if not np.isfinite(point_array).all() or not np.isfinite(distribution_array).all():
            raise ForecastRuntimeError("TimesFM returned non-finite forecast values.")

        device = str(getattr(getattr(model, "model", None), "device", "unknown"))
        latency_ms = (time.perf_counter() - started) * 1_000
        logger.info(
            "forecast_completed",
            extra={
                "model_id": self.settings.model_id,
                "model_revision": self.settings.model_revision,
                "device": device,
                "batch_size": len(requests),
                "max_context_length": max(request.context_length for request in requests),
                "horizon": horizon,
                "latency_ms": round(latency_ms, 2),
            },
        )
        results: list[ForecastResult] = []
        for index, request in enumerate(requests):
            future = None
            if request.timestamps is not None and request.frequency:
                future = build_future_index(
                    request.timestamps[-1], request.frequency, request.horizon
                )
            results.append(
                ForecastResult(
                    future_timestamps=future,
                    point=point_array[index],
                    distribution=distribution_array[index],
                    model_id=self.settings.model_id,
                    model_revision=self.settings.model_revision,
                    device=device,
                    latency_ms=latency_ms,
                )
            )
        return results

    def forecast_with_covariates(self, request: CovariateForecastRequest) -> ForecastResult:
        started = time.perf_counter()
        with self._lock:
            model = self._get_model()
            # XReg needs backcasts, so it recompiles after a standard forecast.
            config = self._make_xreg_config(request)
            model.compile(config)
            self._compile_key = None
            point, distribution = model.forecast_with_covariates(
                inputs=[request.values],
                dynamic_numerical_covariates={
                    name: [np.asarray(values, dtype=float)]
                    for name, values in request.dynamic_numerical.items()
                }
                or None,
                dynamic_categorical_covariates={
                    name: [_encode_categories(values)]
                    for name, values in request.dynamic_categorical.items()
                }
                or None,
                static_numerical_covariates={
                    name: [value] for name, value in request.static_numerical.items()
                }
                or None,
                static_categorical_covariates={
                    name: [_encode_categories([value])[0]]
                    for name, value in request.static_categorical.items()
                }
                or None,
                xreg_mode=request.mode,
                force_on_cpu=True,
            )
        point_array = np.asarray(point[0], dtype=np.float32)
        distribution_array = np.asarray(distribution[0], dtype=np.float32)
        if point_array.shape != (request.horizon,) or distribution_array.shape != (
            request.horizon,
            10,
        ):
            raise ForecastRuntimeError("TimesFM XReg returned an invalid forecast shape.")
        future = None
        if request.timestamps is not None and request.frequency:
            future = build_future_index(request.timestamps[-1], request.frequency, request.horizon)
        device = str(getattr(getattr(model, "model", None), "device", "unknown"))
        return ForecastResult(
            future_timestamps=future,
            point=point_array,
            distribution=distribution_array,
            model_id=self.settings.model_id,
            model_revision=self.settings.model_revision,
            device=device,
            latency_ms=(time.perf_counter() - started) * 1_000,
            warnings=(f"XReg mode: {request.mode}; linear regression forced to CPU.",),
        )

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model
        loader = self._model_loader
        if loader is None:
            import timesfm
            import torch

            torch.set_float32_matmul_precision("high")
            loader = timesfm.TimesFM_2p5_200M_torch.from_pretrained
        self.settings.model_cache.mkdir(parents=True, exist_ok=True)
        try:
            self._model = loader(
                self.settings.model_id,
                revision=self.settings.model_revision,
                cache_dir=str(self.settings.model_cache),
                force_download=False,
                local_files_only=self.settings.offline,
                token=self.settings.hf_token,
                torch_compile=False,
            )
            if self._model_loader is None:
                self._place_model(self._model)
        except Exception as error:
            self._model = None
            raise ForecastRuntimeError(
                "TimesFM checkpoint loading failed "
                f"({type(error).__name__}); check cache access, network, token, and device."
            ) from error
        return self._model

    def _place_model(self, model: Any) -> None:
        import torch

        preference = self.settings.device_preference
        if preference == "cuda" and not torch.cuda.is_available():
            raise ForecastRuntimeError("CUDA was requested but is unavailable.")
        device = (
            "cuda"
            if preference == "cuda" or (preference == "auto" and torch.cuda.is_available())
            else "cpu"
        )
        inner = model.model
        inner.to(torch.device(device))
        inner.device = torch.device(device)
        inner.device_count = torch.cuda.device_count() if device == "cuda" else 1

    def _make_config(self, request: ForecastRequest, *, max_context: int | None = None) -> Any:
        factory = self._config_factory
        if factory is None:
            import timesfm

            factory = timesfm.ForecastConfig
        return factory(
            max_context=max_context or request.compile_context,
            max_horizon=request.compile_horizon,
            normalize_inputs=True,
            per_core_batch_size=1,
            use_continuous_quantile_head=True,
            force_flip_invariance=True,
            infer_is_positive=request.non_negative,
            fix_quantile_crossing=True,
        )

    def _make_xreg_config(self, request: CovariateForecastRequest) -> Any:
        factory = self._config_factory
        if factory is None:
            import timesfm

            factory = timesfm.ForecastConfig
        return factory(
            max_context=request.compile_context,
            max_horizon=request.compile_horizon,
            normalize_inputs=True,
            per_core_batch_size=1,
            use_continuous_quantile_head=True,
            force_flip_invariance=True,
            infer_is_positive=request.non_negative,
            fix_quantile_crossing=True,
            return_backcast=True,
        )


def _encode_categories(values: list[object]) -> list[int]:
    labels = sorted({str(value) for value in values})
    encoding = {label: index for index, label in enumerate(labels)}
    return [encoding[str(value)] for value in values]


def build_future_index(
    last_timestamp: pd.Timestamp, frequency: str, horizon: int
) -> pd.DatetimeIndex:
    try:
        offset = pd.tseries.frequencies.to_offset(frequency)
    except ValueError as error:
        raise ForecastRuntimeError(f"Invalid forecast frequency {frequency!r}.") from error
    return pd.date_range(start=last_timestamp + offset, periods=horizon, freq=offset)
