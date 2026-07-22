from __future__ import annotations

import io
import json
import zipfile
from dataclasses import dataclass
from html import escape

import pandas as pd
import plotly.graph_objects as go


@dataclass(frozen=True)
class ReportBundle:
    forecast_csv: bytes
    metrics_csv: bytes
    anomalies_csv: bytes
    eda_csv: bytes
    html: bytes
    pdf: bytes
    zip_archive: bytes


def _csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8")


def build_report_bundle(
    *,
    title: str,
    forecast: pd.DataFrame,
    metrics: pd.DataFrame,
    anomalies: pd.DataFrame,
    eda_summary: pd.DataFrame,
    figures: list[tuple[str, go.Figure]],
    manifest: dict[str, object],
) -> ReportBundle:
    csv_files = {
        "forecast.csv": _csv_bytes(forecast),
        "metrics.csv": _csv_bytes(metrics),
        "anomalies.csv": _csv_bytes(anomalies),
        "eda_summary.csv": _csv_bytes(eda_summary),
    }
    html = _build_html(title, forecast, metrics, anomalies, eda_summary, figures)
    pdf = _build_pdf(title, forecast, metrics, anomalies, eda_summary)
    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename, payload in csv_files.items():
            archive.writestr(filename, payload)
        archive.writestr("report.html", html)
        archive.writestr("report.pdf", pdf)
        archive.writestr("manifest.json", json.dumps(manifest, indent=2, default=str))
    return ReportBundle(
        forecast_csv=csv_files["forecast.csv"],
        metrics_csv=csv_files["metrics.csv"],
        anomalies_csv=csv_files["anomalies.csv"],
        eda_csv=csv_files["eda_summary.csv"],
        html=html,
        pdf=pdf,
        zip_archive=archive_buffer.getvalue(),
    )


def _build_html(
    title: str,
    forecast: pd.DataFrame,
    metrics: pd.DataFrame,
    anomalies: pd.DataFrame,
    eda: pd.DataFrame,
    figures: list[tuple[str, go.Figure]],
) -> bytes:
    charts: list[str] = []
    for index, (label, figure) in enumerate(figures):
        charts.append(f"<h2>{escape(label)}</h2>")
        charts.append(
            figure.to_html(
                full_html=False,
                include_plotlyjs=index == 0,
                config={"displaylogo": False},
            )
        )
    tables = []
    for label, frame in (
        ("Forecast", forecast),
        ("Performance metrics", metrics),
        ("Anomalies", anomalies),
        ("EDA summary", eda),
    ):
        tables.extend((f"<h2>{label}</h2>", frame.to_html(index=False, escape=True)))
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{escape(title)}</title>
<style>
body{{font-family:Arial,sans-serif;max-width:1200px;margin:2rem auto;color:#0b132b}}
table{{border-collapse:collapse;width:100%;margin-bottom:2rem}}
th,td{{border:1px solid #cbd5e1;padding:.4rem;text-align:right}}
th{{background:#eff6ff}}
</style>
</head><body><h1>{escape(title)}</h1>{"".join(charts)}{"".join(tables)}</body></html>"""
    return document.encode("utf-8")


def _build_pdf(
    title: str,
    forecast: pd.DataFrame,
    metrics: pd.DataFrame,
    anomalies: pd.DataFrame,
    eda: pd.DataFrame,
) -> bytes:
    from reportlab.graphics.charts.lineplots import LinePlot
    from reportlab.graphics.shapes import Drawing
    from reportlab.lib.colors import HexColor
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate

    output = io.BytesIO()
    document = SimpleDocTemplate(output, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    story: list[object] = [Paragraph(escape(title), styles["Title"])]
    numeric = forecast.select_dtypes(include="number")
    if not numeric.empty:
        chart_column = "point_q50" if "point_q50" in numeric else numeric.columns[0]
        series = numeric[chart_column].head(200).to_numpy(dtype=float)
        drawing = Drawing(700, 220)
        chart = LinePlot()
        chart.x, chart.y, chart.width, chart.height = 50, 30, 620, 170
        chart.data = [[(index + 1, value) for index, value in enumerate(series)]]
        chart.lines[0].strokeColor = HexColor("#0284c7")
        drawing.add(chart)
        story.extend((Paragraph("Forecast chart", styles["Heading2"]), drawing))
    for label, frame in (
        ("Forecast", forecast),
        ("Performance metrics", metrics),
        ("Anomalies", anomalies),
        ("EDA summary", eda),
    ):
        story.extend((Paragraph(label, styles["Heading2"]), _pdf_table(frame), PageBreak()))
    document.build(story[:-1])
    return output.getvalue()


def _pdf_table(frame: pd.DataFrame):
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    display = frame.head(100).copy()
    rows = [list(map(str, display.columns))] + [list(map(str, row)) for row in display.values]
    if len(rows) == 1:
        rows.append(["No data"] + [""] * max(len(display.columns) - 1, 0))
    table = Table(rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbeafe")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return table
