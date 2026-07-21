from __future__ import annotations

import streamlit as st

from timesfm_app.config import AppSettings
from timesfm_app.contracts import ResolvedAsset
from timesfm_app.ingestion.providers import (
    list_huggingface_files,
    resolve_huggingface_file,
    resolve_kaggle_dataset,
)
from timesfm_app.ingestion.resolvers import cache_uploaded_file, download_public_url


def render_source_selector(settings: AppSettings) -> ResolvedAsset | None:
    source = st.radio(
        "Data source",
        ["Upload", "Public URL", "Kaggle", "Hugging Face"],
        horizontal=True,
        key="source_kind",
    )
    try:
        if source == "Upload":
            _render_upload(settings)
        elif source == "Public URL":
            _render_url(settings)
        elif source == "Kaggle":
            _render_kaggle(settings)
        else:
            _render_huggingface(settings)
    except Exception as error:
        st.error(str(error))
    return st.session_state.get("resolved_asset")


def _render_upload(settings: AppSettings) -> None:
    uploaded = st.file_uploader(
        "Upload CSV, Parquet, or XLSX",
        type=["csv", "parquet", "xlsx"],
        key="dataset_upload",
    )
    if uploaded is not None:
        st.session_state.resolved_asset = cache_uploaded_file(
            uploaded.name,
            uploaded.getvalue(),
            settings.data_cache / "uploads",
        )


def _render_url(settings: AppSettings) -> None:
    url = st.text_input("Dataset URL", placeholder="https://example.com/series.csv")
    if st.button("Download URL", key="download_url"):
        if settings.offline:
            raise ValueError("URL downloads are unavailable in offline mode.")
        st.session_state.resolved_asset = download_public_url(
            url,
            settings.data_cache / "urls",
        )


def _render_kaggle(settings: AppSettings) -> None:
    handle = st.text_input("Kaggle dataset", placeholder="owner/dataset/versions/1")
    relative_path = st.text_input("File path (optional)")
    if st.button("Download Kaggle dataset", key="download_kaggle"):
        _configure_kaggle(settings)
        assets = resolve_kaggle_dataset(handle, path=relative_path or None)
        st.session_state.kaggle_assets = assets
        st.session_state.resolved_asset = assets[0]
    assets = st.session_state.get("kaggle_assets", [])
    if len(assets) > 1:
        selected = st.selectbox(
            "Dataset file",
            options=assets,
            format_func=lambda asset: asset.path.name,
            key="kaggle_file",
        )
        st.session_state.resolved_asset = selected


def _render_huggingface(settings: AppSettings) -> None:
    repo_id = st.text_input("Dataset repository", placeholder="owner/dataset")
    revision = st.text_input("Revision (optional)")
    if st.button("List repository files", key="list_hf_files"):
        if settings.offline:
            raise ValueError("Repository listing is unavailable in offline mode.")
        st.session_state.hf_files = list_huggingface_files(
            repo_id,
            revision=revision or None,
            token=settings.hf_token,
        )
    files = st.session_state.get("hf_files", [])
    if files:
        filename = st.selectbox("Dataset file", files, key="hf_file")
        if st.button("Download Hugging Face file", key="download_hf"):
            st.session_state.resolved_asset = resolve_huggingface_file(
                repo_id,
                filename,
                settings.data_cache / "huggingface",
                revision=revision or None,
                token=settings.hf_token,
                offline=settings.offline,
            )


def _configure_kaggle(settings: AppSettings) -> None:
    if not settings.kaggle_api_token and not (settings.kaggle_username and settings.kaggle_key):
        return
    import kagglehub

    if settings.kaggle_api_token:
        kagglehub.config.set_kaggle_api_token(settings.kaggle_api_token)
    else:
        kagglehub.config.set_kaggle_credentials(settings.kaggle_username, settings.kaggle_key)
