from __future__ import annotations

from pathlib import Path

import streamlit as st

from timesfm_app.contracts import ForecastRequest, SeriesSpec
from timesfm_app.forecasting.preprocessing import prepare_series
from timesfm_app.ingestion.readers import list_excel_sheets, read_tabular
from timesfm_app.ui.charts import build_forecast_chart
from timesfm_app.ui.results import forecast_frame
from timesfm_app.ui.runtime import get_runtime, load_settings
from timesfm_app.ui.source_controls import render_source_selector


@st.cache_data(show_spinner=False)
def _load_frame(path: str, sha256: str, sheet_name: str | None):
    del sha256
    return read_tabular(Path(path), sheet_name=sheet_name)


def render_dataset_page() -> None:
    st.subheader("Forecast a dataset")
    asset = render_source_selector(load_settings())
    if asset is None:
        st.caption("Choose a source to inspect its columns and configure a forecast.")
        return
    st.caption(
        f"Loaded {asset.path.name} · {asset.size_bytes:,} bytes · SHA-256 {asset.sha256[:12]}…"
    )
    try:
        sheets = list_excel_sheets(asset.path)
        sheet = st.selectbox("Worksheet", sheets) if sheets else None
        frame = _load_frame(str(asset.path), asset.sha256, sheet)
    except Exception as error:
        st.error(f"Could not read dataset: {error}")
        return

    st.dataframe(frame.head(100), width="stretch", hide_index=True)
    if len(frame) < 2 or len(frame.columns) < 2:
        st.error("Dataset needs at least two rows and two columns.")
        return

    left, right = st.columns(2)
    date_column = left.selectbox("Date/time column", list(frame.columns))
    target_options = [column for column in frame.columns if column != date_column]
    target_column = right.selectbox("Target column", target_options)

    settings = load_settings()
    maximum_context = min(len(frame), settings.max_context_length)
    controls = st.columns(4)
    context_length = controls[0].number_input(
        "Context length",
        min_value=2,
        max_value=maximum_context,
        value=min(1_024, maximum_context),
    )
    horizon = controls[1].number_input(
        "Forecast horizon",
        min_value=1,
        max_value=1_024,
        value=24,
        key="dataset_horizon",
    )
    frequency_mode = controls[2].selectbox(
        "Frequency", ["Auto", "h", "D", "W", "MS", "ME", "QS", "YS"]
    )
    non_negative = controls[3].checkbox("Target cannot be negative")

    if not st.button("Forecast dataset", type="primary"):
        return
    try:
        prepared = prepare_series(
            frame,
            SeriesSpec(
                date_column=str(date_column),
                target_column=str(target_column),
                context_length=int(context_length),
                frequency=None if frequency_mode == "Auto" else frequency_mode,
            ),
        )
        request = ForecastRequest(
            values=prepared.values,
            context_length=len(prepared.values),
            horizon=int(horizon),
            timestamps=prepared.timestamps,
            frequency=prepared.frequency,
            non_negative=non_negative,
        )
        with st.spinner("Forecasting…"):
            result = get_runtime().forecast(request)
    except Exception as error:
        st.error(str(error))
        return

    for warning in prepared.report.warnings:
        st.warning(warning)
    st.caption(
        f"{prepared.report.usable_rows:,} context rows · "
        f"{prepared.report.internal_missing_values:,} internal missing values · "
        f"frequency {prepared.frequency}"
    )
    st.plotly_chart(
        build_forecast_chart(prepared.timestamps, prepared.values, result),
        width="stretch",
        config={"displaylogo": False},
    )
    st.dataframe(forecast_frame(result), width="stretch", hide_index=True)
    st.caption(
        f"{result.model_id} · {result.device} · {result.latency_ms:,.0f} ms · "
        f"revision {result.model_revision[:8]}"
    )
