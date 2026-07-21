from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from predictor import DeviceChoice
from timesfm_app.config import AppSettings


@dataclass(frozen=True)
class ForecastControls:
    device: DeviceChoice
    context_length: int
    horizon: int
    frequency: str | None


def render_sidebar(settings: AppSettings) -> ForecastControls:
    with st.sidebar:
        st.header("Forecast controls")
        device = st.selectbox("Compute device", ["auto", "cpu", "cuda"], index=0)
        context = st.number_input(
            "Context length",
            min_value=2,
            max_value=settings.max_context_length,
            value=1_024,
            step=32,
        )
        horizon = st.number_input(
            "Forecast horizon", min_value=1, max_value=1_024, value=24, step=1
        )
        frequency_label = st.selectbox(
            "Frequency",
            [
                "Auto",
                "Hourly",
                "Daily",
                "Weekly",
                "Month start",
                "Month end",
                "Quarterly",
                "Yearly",
            ],
        )
        frequency_map = {
            "Auto": None,
            "Hourly": "h",
            "Daily": "D",
            "Weekly": "W",
            "Month start": "MS",
            "Month end": "ME",
            "Quarterly": "QS",
            "Yearly": "YS",
        }
        st.divider()
        st.subheader("API configuration")
        kaggle_ready = bool(
            settings.kaggle_api_token or (settings.kaggle_username and settings.kaggle_key)
        )
        st.caption(f"Kaggle: {'configured' if kaggle_ready else 'not configured'}")
        st.caption(f"Hugging Face: {'token configured' if settings.hf_token else 'public access'}")
        st.caption(f"Offline mode: {'on' if settings.offline else 'off'}")
        st.caption(f"Checkpoint: {settings.model_id}")
    return ForecastControls(
        device=device,
        context_length=int(context),
        horizon=int(horizon),
        frequency=frequency_map[frequency_label],
    )
