from __future__ import annotations

import io
import json
import zipfile

import pandas as pd
import plotly.graph_objects as go

from timesfm_app.reports import build_report_bundle


def test_report_bundle_contains_direct_csv_html_pdf_and_provenance_zip() -> None:
    forecast = pd.DataFrame({"timestamp": ["2025-01-01"], "point_q50": [2.5]})
    metrics = pd.DataFrame({"metric": ["mae"], "value": [0.4]})
    anomalies = pd.DataFrame({"timestamp": ["2025-01-01"], "is_anomaly": [False]})
    eda = pd.DataFrame({"metric": ["mean"], "value": [2.0]})
    figure = go.Figure(go.Scatter(x=[1, 2], y=[2, 3]))

    bundle = build_report_bundle(
        title="Demand <forecast>",
        forecast=forecast,
        metrics=metrics,
        anomalies=anomalies,
        eda_summary=eda,
        figures=[("Forecast", figure)],
        manifest={"model_revision": "abc", "horizon": 1},
    )

    assert bundle.forecast_csv.startswith(b"timestamp,point_q50")
    assert b"<html" in bundle.html.lower()
    assert b"plotly" in bundle.html.lower()
    assert bundle.pdf.startswith(b"%PDF")
    with zipfile.ZipFile(io.BytesIO(bundle.zip_archive)) as archive:
        assert set(archive.namelist()) == {
            "forecast.csv",
            "metrics.csv",
            "anomalies.csv",
            "eda_summary.csv",
            "report.html",
            "report.pdf",
            "manifest.json",
        }
        assert json.loads(archive.read("manifest.json"))["model_revision"] == "abc"
        assert b"Demand &lt;forecast&gt;" in archive.read("report.html")
