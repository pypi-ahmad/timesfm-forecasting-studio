from __future__ import annotations

import streamlit as st

from predictor import DeviceChoice, TimesFMPredictor
from timesfm_app.config import AppSettings
from timesfm_app.forecasting.runtime import TimesFMRuntime


def load_settings() -> AppSettings:
    try:
        secrets = dict(st.secrets)
    except FileNotFoundError:
        secrets = {}
    return AppSettings.from_environment(secrets=secrets)


@st.cache_resource(show_spinner="Loading TimesFM 2.5 checkpoint…")
def get_runtime() -> TimesFMRuntime:
    return TimesFMRuntime(load_settings())


@st.cache_resource(show_spinner="Loading TimesFM 2.5 checkpoint…")
def get_predictor(device: DeviceChoice) -> TimesFMPredictor:
    return TimesFMPredictor(load_settings(), device=device)
