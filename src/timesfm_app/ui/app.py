from __future__ import annotations

import streamlit as st

from timesfm_app.ui.controls import render_sidebar
from timesfm_app.ui.forecast_page import render_forecast_page
from timesfm_app.ui.loading_page import render_loading_page
from timesfm_app.ui.manual_page import render_manual_page
from timesfm_app.ui.runtime import load_settings


def render_app() -> None:
    st.set_page_config(page_title="TimesFM Forecast Studio", page_icon="📈", layout="wide")
    _apply_theme()
    st.title("TimesFM Forecast Studio")
    st.caption("Local-first, zero-shot univariate forecasting with Google TimesFM 2.5")
    controls = render_sidebar(load_settings())

    loading_tab, forecast_tab, manual_tab = st.tabs(
        ["Data Loading", "Interactive Forecasting Charts", "Manual Simulator"]
    )
    with loading_tab:
        render_loading_page(load_settings())
    with forecast_tab:
        render_forecast_page(controls)
    with manual_tab:
        render_manual_page(controls)


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
