from __future__ import annotations

import streamlit as st

from timesfm_app.ui.controls import render_sidebar
from timesfm_app.ui.manual_page import render_manual_page
from timesfm_app.ui.runtime import load_settings
from timesfm_app.ui.workbench_page import render_workbench_stage


def render_app() -> None:
    st.set_page_config(page_title="TimesFM Forecast Studio", page_icon="📈", layout="wide")
    _apply_theme()
    st.title("TimesFM Forecast Studio")
    st.caption("Local-first, zero-shot univariate forecasting with Google TimesFM 2.5")
    controls = render_sidebar(load_settings())
    stage = st.segmented_control(
        "Workflow stage",
        ["Load & configure", "Analyze", "Forecast", "Evaluate & anomalies", "Export"],
        default="Load & configure",
        key="workflow_stage",
    )
    manual = st.sidebar.toggle("Manual simulator", value=False)
    if manual:
        render_manual_page(controls)
        return
    render_workbench_stage(stage or "Load & configure", controls, load_settings())


def _apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root { --ink: #0b132b; --accent: #2563eb; --signal: #0891b2; }
        .stApp { background: linear-gradient(180deg, #f8fafc 0%, #ffffff 26rem); }
        h1, h2, h3 { color: var(--ink); letter-spacing: -0.025em; }
        [data-testid="stSidebar"] { border-right: 1px solid #dbeafe; }
        [data-testid="stMetric"] { border-left: 3px solid var(--signal); padding-left: 0.8rem; }
        .stButton > button[kind="primary"] {
            background: var(--accent); border-color: var(--accent); font-weight: 650;
        }
        .stTabs [data-baseweb="tab-list"] { gap: 1.25rem; }
        .stTabs [aria-selected="true"] { color: var(--accent); }
        code, [data-testid="stCaptionContainer"] { font-family: "Cascadia Code", monospace; }
        </style>
        """,
        unsafe_allow_html=True,
    )
