from __future__ import annotations

import numpy as np
import streamlit as st

from timesfm_app.contracts import ForecastRequest
from timesfm_app.forecasting.preprocessing import parse_manual_values
from timesfm_app.ui.charts import build_forecast_chart
from timesfm_app.ui.results import forecast_frame
from timesfm_app.ui.runtime import get_runtime


def render_quick_page() -> None:
    st.subheader("Quick numeric forecast")
    st.caption("Paste comma- or newline-separated observations. No timestamps required.")
    values_text = st.text_area(
        "Historical values",
        value="10, 12, 15, 14, 18",
        height=120,
        key="quick_values",
    )
    controls = st.columns(2)
    horizon = controls[0].number_input(
        "Forecast horizon",
        min_value=1,
        max_value=1_024,
        value=10,
        key="quick_horizon",
    )
    non_negative = controls[1].checkbox(
        "Target cannot be negative",
        value=False,
        key="quick_non_negative",
    )

    if not st.button("Forecast values", type="primary", key="quick_forecast"):
        return
    try:
        values = parse_manual_values(values_text)
        request = ForecastRequest(
            values=values,
            context_length=len(values),
            horizon=int(horizon),
            non_negative=non_negative,
        )
        with st.spinner("Forecasting…"):
            result = get_runtime().forecast(request)
    except Exception as error:
        st.error(str(error))
        return

    if len(values) < 32:
        st.warning("Context has fewer than 32 observations; forecast quality may be weak.")
    history_x = np.arange(len(values))
    st.plotly_chart(
        build_forecast_chart(history_x, values, result),
        width="stretch",
        config={"displaylogo": False},
    )
    st.dataframe(forecast_frame(result), width="stretch", hide_index=True)
    st.caption(
        f"{result.model_id} · {result.device} · {result.latency_ms:,.0f} ms · "
        f"revision {result.model_revision[:8]}"
    )
