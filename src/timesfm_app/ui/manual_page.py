from __future__ import annotations

import numpy as np
import streamlit as st

from timesfm_app.contracts import ForecastRequest
from timesfm_app.forecasting.preprocessing import parse_manual_values
from timesfm_app.ui.charts import build_forecast_chart
from timesfm_app.ui.controls import ForecastControls
from timesfm_app.ui.runtime import get_predictor


def render_manual_page(controls: ForecastControls) -> None:
    st.subheader("Manual forecast simulator")
    values_text = st.text_area("Historical values", value="10, 12, 15, 14, 18", height=140)
    non_negative = st.checkbox("Target cannot be negative", key="manual_positive")
    if not st.button("Forecast values", type="primary"):
        return
    try:
        values = parse_manual_values(values_text)
        context = min(len(values), controls.context_length)
        output = get_predictor(controls.device).predict(
            ForecastRequest(
                values=values,
                context_length=context,
                horizon=controls.horizon,
                non_negative=non_negative,
            )
        )
        figure = build_forecast_chart(np.arange(len(values)), values, output.result)
        st.plotly_chart(figure, width="stretch", config={"displaylogo": False})
        st.dataframe(output.frame, width="stretch", hide_index=True)
    except Exception as error:
        st.error(f"Manual forecast failed: {error}")
