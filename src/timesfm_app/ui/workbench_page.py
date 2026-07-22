from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from loader import load_dataset
from timesfm_app.analysis import EdaResult, analyze_series
from timesfm_app.config import AppSettings
from timesfm_app.contracts import ForecastRequest, PreparedSeries, SeriesSpec
from timesfm_app.evaluation import BacktestResult, run_rolling_backtest
from timesfm_app.forecasting.preprocessing import prepare_series
from timesfm_app.reports import build_report_bundle
from timesfm_app.ui.charts import build_forecast_chart
from timesfm_app.ui.controls import ForecastControls
from timesfm_app.ui.forecast_page import render_forecast_page
from timesfm_app.ui.loading_page import loaded_assets, render_loading_page
from timesfm_app.ui.runtime import get_predictor


def render_workbench_stage(stage: str, controls: ForecastControls, settings: AppSettings) -> None:
    if stage == "Load & configure":
        render_loading_page(settings)
    elif stage == "Analyze":
        _render_analysis(controls)
    elif stage == "Forecast":
        render_forecast_page(controls)
    elif stage == "Evaluate & anomalies":
        _render_evaluation(controls)
    else:
        _render_export()


def _active_series(controls: ForecastControls) -> tuple[str, str, PreparedSeries] | None:
    inventory = loaded_assets()
    if not inventory:
        st.info("Load a dataset in the Load & configure stage first.")
        return None
    dataset_id = st.selectbox(
        "Active dataset",
        list(inventory),
        format_func=lambda key: inventory[key].path.name,
        key="active_dataset",
    )
    dataset = load_dataset(inventory[dataset_id])
    columns = [str(column) for column in dataset.frame.columns]
    default_date = dataset.datetime_columns[0] if dataset.datetime_columns else columns[0]
    date_column = st.selectbox(
        "Date/time column", columns, index=columns.index(default_date), key="active_date"
    )
    targets = [column for column in columns if column != date_column]
    numeric = [column for column in targets if pd.api.types.is_numeric_dtype(dataset.frame[column])]
    target_column = st.selectbox(
        "Target column",
        targets,
        index=targets.index(numeric[0] if numeric else targets[0]),
        key="active_target",
    )
    try:
        prepared = prepare_series(
            dataset.frame,
            SeriesSpec(date_column, target_column, controls.context_length, controls.frequency),
        )
    except Exception as error:
        st.error(str(error))
        return None
    return dataset_id, target_column, prepared


def _default_seasonal_period(frequency: str) -> int:
    normalized = frequency.lower()
    if "min" in normalized or normalized in {"h", "hour"}:
        return 24
    if normalized.startswith("d"):
        return 7
    if normalized.startswith("w"):
        return 52
    if normalized.startswith("m"):
        return 12
    if normalized.startswith("q"):
        return 4
    return 7


def _render_analysis(controls: ForecastControls) -> None:
    st.subheader("Comprehensive time-series analysis")
    active = _active_series(controls)
    if active is None:
        return
    dataset_id, target, prepared = active
    seasonal_period = st.number_input(
        "Seasonal period",
        min_value=2,
        max_value=max(2, min(10_000, len(prepared.values) // 2)),
        value=min(_default_seasonal_period(prepared.frequency), max(2, len(prepared.values) // 2)),
    )
    result = analyze_series(
        prepared.timestamps, prepared.values, seasonal_period=int(seasonal_period)
    )
    st.session_state.eda_result = result
    st.session_state.eda_dataset_id = dataset_id
    st.session_state.eda_target = target
    with st.container(horizontal=True):
        for label in ("count", "missing", "mean", "std", "median", "iqr"):
            value = result.summary[label]
            st.metric(
                label.replace("_", " ").title(),
                f"{value:,.4g}" if isinstance(value, float) else f"{value:,}",
                border=True,
            )
    _render_eda_charts(result)
    st.dataframe(
        pd.DataFrame({"metric": result.summary.keys(), "value": result.summary.values()}),
        hide_index=True,
    )
    for note in result.notes:
        st.info(note)


def _render_eda_charts(result: EdaResult) -> None:
    trend = px.line(
        result.trend, x="timestamp", y=["value", "rolling_mean"], title="Trend and rolling mean"
    )
    st.plotly_chart(trend, config={"displaylogo": False})
    left, right = st.columns(2)
    left.plotly_chart(
        px.histogram(result.distribution, x="value", marginal="box", title="Distribution"),
        config={"displaylogo": False},
    )
    ecdf = px.ecdf(result.distribution, x="value", title="Empirical cumulative distribution")
    right.plotly_chart(ecdf, config={"displaylogo": False})
    if not result.seasonal_profile.empty:
        st.plotly_chart(
            px.line(
                result.seasonal_profile,
                x="seasonal_position",
                y="mean",
                markers=True,
                title="Seasonal profile",
            ),
            config={"displaylogo": False},
        )
    if not result.acf.empty:
        st.plotly_chart(
            px.bar(result.acf, x="lag", y="acf", title="Autocorrelation"),
            config={"displaylogo": False},
        )
    if not result.decomposition.empty:
        melted = result.decomposition.melt(
            id_vars="timestamp", var_name="component", value_name="value"
        )
        st.plotly_chart(
            px.line(
                melted, x="timestamp", y="value", facet_row="component", title="STL decomposition"
            ),
            config={"displaylogo": False},
        )
    st.dataframe(result.outliers[result.outliers["is_outlier"]], hide_index=True)


def _render_evaluation(controls: ForecastControls) -> None:
    st.subheader("Rolling backtest and forecast anomalies")
    active = _active_series(controls)
    if active is None:
        return
    dataset_id, _, prepared = active
    windows = st.slider("Backtest windows", 1, 10, 3)
    if st.button("Run rolling backtest", type="primary"):

        def forecast(context, horizon):
            request = ForecastRequest(
                values=context,
                context_length=len(context),
                horizon=horizon,
                non_negative=False,
            )
            return get_predictor(controls.device).runtime.forecast(request)

        try:
            with st.spinner("Running rolling-origin evaluation…"):
                result = run_rolling_backtest(
                    prepared.timestamps,
                    prepared.values,
                    horizon=controls.horizon,
                    windows=windows,
                    context_length=controls.context_length,
                    forecast=forecast,
                )
            st.session_state.backtest_result = result
            st.session_state.backtest_dataset_id = dataset_id
        except Exception as error:
            st.error(str(error))
    result: BacktestResult | None = st.session_state.get("backtest_result")
    if result is None or st.session_state.get("backtest_dataset_id") != dataset_id:
        return
    st.dataframe(result.metrics, hide_index=True)
    st.plotly_chart(
        px.line(
            result.predictions,
            x="timestamp",
            y=["actual", "point_q50"],
            color="window",
            title="Rolling-origin predictions",
        ),
        config={"displaylogo": False},
    )
    anomalies = result.anomalies[result.anomalies["is_anomaly"]]
    st.metric("Interval anomalies", len(anomalies), border=True)
    st.dataframe(anomalies, hide_index=True)


def _render_export() -> None:
    st.subheader("Export forecast workbench outputs")
    inventory = loaded_assets()
    outputs = st.session_state.get("forecast_outputs", {})
    if not outputs:
        st.info("Generate a forecast before exporting reports.")
        return
    dataset_id = st.selectbox(
        "Dataset output", list(outputs), format_func=lambda key: inventory[key].path.name
    )
    output = outputs[dataset_id]
    history = st.session_state.forecast_histories[dataset_id]
    backtest: BacktestResult | None = st.session_state.get("backtest_result")
    eda: EdaResult | None = st.session_state.get("eda_result")
    metrics = backtest.metrics if backtest is not None else pd.DataFrame()
    anomalies = backtest.anomalies if backtest is not None else pd.DataFrame()
    eda_frame = (
        pd.DataFrame({"metric": eda.summary.keys(), "value": eda.summary.values()})
        if eda is not None
        else pd.DataFrame()
    )
    figure = build_forecast_chart(history.timestamps, history.values, output.result)
    bundle = build_report_bundle(
        title=f"TimesFM report — {inventory[dataset_id].path.name}",
        forecast=output.frame,
        metrics=metrics,
        anomalies=anomalies,
        eda_summary=eda_frame,
        figures=[("Forecast", figure)],
        manifest={
            "dataset_sha256": dataset_id,
            "model_id": output.result.model_id,
            "model_revision": output.result.model_revision,
            "device": output.result.device,
        },
    )
    name = inventory[dataset_id].path.stem
    with st.container(horizontal=True):
        st.download_button(
            "Forecast CSV",
            bundle.forecast_csv,
            f"{name}-forecast.csv",
            "text/csv",
            on_click="ignore",
        )
        st.download_button(
            "Interactive HTML", bundle.html, f"{name}-report.html", "text/html", on_click="ignore"
        )
        st.download_button(
            "PDF report", bundle.pdf, f"{name}-report.pdf", "application/pdf", on_click="ignore"
        )
        st.download_button(
            "Complete ZIP",
            bundle.zip_archive,
            f"{name}-report.zip",
            "application/zip",
            on_click="ignore",
        )
