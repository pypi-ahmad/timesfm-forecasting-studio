from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from loader import LoadedDataset, load_dataset, workbook_sheets
from predictor import PredictionOutput
from timesfm_app.contracts import ForecastRequest, PreparedSeries, ResolvedAsset, SeriesSpec
from timesfm_app.forecasting.preprocessing import prepare_series
from timesfm_app.ui.charts import build_forecast_chart
from timesfm_app.ui.controls import ForecastControls
from timesfm_app.ui.loading_page import loaded_assets
from timesfm_app.ui.runtime import get_predictor


@dataclass(frozen=True)
class DatasetMapping:
    dataset: LoadedDataset
    date_column: str
    target_column: str
    non_negative: bool


@st.cache_data(show_spinner=False)
def _load_asset(asset: ResolvedAsset, sheet_name: str | None) -> LoadedDataset:
    return load_dataset(asset, sheet_name=sheet_name)


def build_forecast_request(
    dataset: LoadedDataset,
    *,
    date_column: str,
    target_column: str,
    controls: ForecastControls,
    non_negative: bool,
) -> tuple[ForecastRequest, PreparedSeries]:
    prepared = prepare_series(
        dataset.frame,
        SeriesSpec(
            date_column=date_column,
            target_column=target_column,
            context_length=controls.context_length,
            frequency=controls.frequency,
        ),
    )
    request = ForecastRequest(
        values=prepared.values,
        context_length=len(prepared.values),
        horizon=controls.horizon,
        timestamps=prepared.timestamps,
        frequency=prepared.frequency,
        non_negative=non_negative,
    )
    return request, prepared


def render_forecast_page(controls: ForecastControls) -> None:
    st.subheader("Interactive forecasting charts")
    inventory = loaded_assets()
    if not inventory:
        st.info("Load one or more datasets in the Data Loading tab.")
        return

    mappings: dict[str, DatasetMapping] = {}
    setup_errors: dict[str, str] = {}
    for dataset_id, asset in inventory.items():
        try:
            mapping = _render_mapping(dataset_id, asset)
            if mapping is not None:
                mappings[dataset_id] = mapping
        except Exception as error:
            setup_errors[dataset_id] = f"{type(error).__name__}: {error}"
            st.error(f"{asset.path.name}: {setup_errors[dataset_id]}")

    if st.button("Forecast all datasets", type="primary", disabled=not mappings):
        _run_all(mappings, setup_errors, controls)
    _render_selected_result(inventory)


def _render_mapping(dataset_id: str, asset: ResolvedAsset) -> DatasetMapping | None:
    with st.expander(asset.path.name, expanded=len(loaded_assets()) <= 3):
        sheets = workbook_sheets(asset)
        sheet = None
        if sheets:
            sheet = st.selectbox("Worksheet", sheets, key=f"sheet_{dataset_id}")
        dataset = _load_asset(asset, sheet)
        if len(dataset.frame) < 2 or len(dataset.frame.columns) < 2:
            st.error("Dataset needs at least two rows and two columns.")
            return None
        st.dataframe(dataset.frame.head(20), width="stretch", hide_index=True)
        columns = [str(column) for column in dataset.frame.columns]
        default_date = dataset.datetime_columns[0] if dataset.datetime_columns else columns[0]
        date_column = st.selectbox(
            "Date/time column",
            columns,
            index=columns.index(default_date),
            key=f"date_{dataset_id}_{sheet}",
        )
        targets = [column for column in columns if column != date_column]
        numeric = [
            column
            for column in targets
            if pd.api.types.is_numeric_dtype(dataset.frame[column].dtype)
        ]
        default_target = numeric[0] if numeric else targets[0]
        target_column = st.selectbox(
            "Target column",
            targets,
            index=targets.index(default_target),
            key=f"target_{dataset_id}_{sheet}",
        )
        non_negative = st.checkbox(
            "Target cannot be negative", key=f"positive_{dataset_id}_{sheet}"
        )
        if dataset.datetime_columns:
            st.caption(f"Detected datetime candidates: {', '.join(dataset.datetime_columns)}")
        else:
            st.warning("No datetime column was confidently detected; verify the selection.")
        return DatasetMapping(dataset, date_column, target_column, non_negative)


def _run_all(
    mappings: dict[str, DatasetMapping],
    setup_errors: dict[str, str],
    controls: ForecastControls,
) -> None:
    progress = st.progress(0, text="Validating datasets…")
    requests: dict[str, ForecastRequest] = {}
    histories: dict[str, PreparedSeries] = {}
    errors = dict(setup_errors)
    for index, (dataset_id, mapping) in enumerate(mappings.items(), start=1):
        try:
            request, prepared = build_forecast_request(
                mapping.dataset,
                date_column=mapping.date_column,
                target_column=mapping.target_column,
                controls=controls,
                non_negative=mapping.non_negative,
            )
            requests[dataset_id] = request
            histories[dataset_id] = prepared
        except Exception as error:
            errors[dataset_id] = f"{type(error).__name__}: {error}"
        progress.progress(index / max(len(mappings), 1) * 0.4, text="Validating datasets…")
    outputs: dict[str, PredictionOutput] = {}
    if requests:
        progress.progress(0.5, text="Running TimesFM inference…")
        batch = get_predictor(controls.device).predict_many(requests)
        outputs.update(batch.forecasts)
        errors.update(batch.errors)
    progress.progress(1.0, text="Forecasting complete")
    st.session_state.forecast_outputs = outputs
    st.session_state.forecast_errors = errors
    st.session_state.forecast_histories = histories


def _render_selected_result(inventory: dict[str, ResolvedAsset]) -> None:
    outputs: dict[str, PredictionOutput] = st.session_state.get("forecast_outputs", {})
    errors: dict[str, str] = st.session_state.get("forecast_errors", {})
    available = [
        dataset_id for dataset_id in inventory if dataset_id in outputs or dataset_id in errors
    ]
    if not available:
        return
    st.divider()
    selected_id = st.selectbox(
        "Dataset result",
        available,
        format_func=lambda dataset_id: inventory[dataset_id].path.name,
    )
    if selected_id in errors:
        st.error(errors[selected_id])
        return
    output = outputs[selected_id]
    prepared: PreparedSeries = st.session_state.forecast_histories[selected_id]
    for warning in prepared.report.warnings:
        st.warning(warning)
    try:
        figure = build_forecast_chart(prepared.timestamps, prepared.values, output.result)
        st.plotly_chart(figure, width="stretch", config={"displaylogo": False})
    except Exception as error:
        st.error(f"Forecast chart rendering failed ({type(error).__name__}): {error}")
    st.dataframe(output.frame, width="stretch", hide_index=True)
    st.caption(
        f"{output.result.model_id} · {output.result.device} · "
        f"{output.result.latency_ms:,.0f} ms · revision {output.result.model_revision[:8]}"
    )
