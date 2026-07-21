from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import plotly.graph_objects as go

from timesfm_app.contracts import ForecastResult


def build_forecast_chart(
    history_x: Sequence[object],
    history_values: np.ndarray,
    result: ForecastResult,
) -> go.Figure:
    future_x: Sequence[object]
    if result.future_timestamps is None:
        future_x = list(range(len(history_values), len(history_values) + len(result.point)))
    else:
        future_x = result.future_timestamps

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=history_x, y=history_values, mode="lines", name="History", line={"color": "#64748b"}
        )
    )
    figure.add_trace(
        go.Scatter(
            x=future_x,
            y=result.distribution[:, 1],
            mode="lines",
            name="q10",
            line={"width": 0},
            hoverinfo="skip",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=future_x,
            y=result.distribution[:, 9],
            mode="lines",
            name="q90",
            fill="tonexty",
            fillcolor="rgba(14, 165, 233, 0.18)",
            line={"width": 0},
            hoverinfo="skip",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=future_x,
            y=result.point,
            mode="lines+markers",
            name="Forecast (q50)",
            line={"color": "#0284c7", "width": 3},
        )
    )
    figure.update_layout(
        hovermode="x unified",
        template="plotly_white",
        margin={"l": 12, "r": 12, "t": 24, "b": 12},
        xaxis_title=None,
        yaxis_title=None,
        legend={"orientation": "h", "y": 1.05},
    )
    figure.add_vrect(
        x0=future_x[0],
        x1=future_x[-1],
        fillcolor="rgba(37, 99, 235, 0.06)",
        line_width=0,
        layer="below",
    )
    return figure
