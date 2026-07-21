from __future__ import annotations

import pandas as pd
import streamlit as st

from integrations import HuggingFaceDatasetClient, KaggleDatasetClient
from loader import UploadPayload, cache_uploads
from timesfm_app.config import AppSettings
from timesfm_app.contracts import ResolvedAsset
from timesfm_app.ingestion.resolvers import download_public_url


def loaded_assets() -> dict[str, ResolvedAsset]:
    return st.session_state.setdefault("loaded_assets", {})


def render_loading_page(settings: AppSettings) -> None:
    st.subheader("Load time-series datasets")
    source = st.radio(
        "Data source",
        ["Upload", "Public URL", "Kaggle", "Hugging Face"],
        horizontal=True,
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
    _render_inventory()


def _add_assets(assets: list[ResolvedAsset]) -> None:
    inventory = loaded_assets()
    for asset in assets:
        inventory[asset.sha256] = asset


def _render_upload(settings: AppSettings) -> None:
    uploads = st.file_uploader(
        "Upload datasets",
        type=["csv", "parquet", "xlsx"],
        accept_multiple_files=True,
    )
    if uploads:
        payloads = [UploadPayload(item.name, item.getvalue()) for item in uploads]
        assets = cache_uploads(payloads, settings.data_cache / "uploads")
        _add_assets(assets)
        st.success(f"Loaded {len(assets)} file(s).")


def _render_url(settings: AppSettings) -> None:
    url = st.text_input("Dataset URL", placeholder="https://example.com/series.csv")
    if st.button("Download URL"):
        if settings.offline:
            raise ValueError("URL downloads are unavailable in offline mode.")
        _add_assets([download_public_url(url, settings.data_cache / "urls")])


def _render_kaggle(settings: AppSettings) -> None:
    client = KaggleDatasetClient(settings)
    query = st.text_input("Search Kaggle datasets")
    if st.button("Search Kaggle"):
        st.session_state.kaggle_results = client.search(query)
    results = st.session_state.get("kaggle_results", [])
    if results:
        selected = st.selectbox(
            "Kaggle result", results, format_func=lambda item: f"{item.title} · {item.dataset_id}"
        )
        if st.button("Download Kaggle dataset"):
            _add_assets(client.download(selected.dataset_id))


def _render_huggingface(settings: AppSettings) -> None:
    client = HuggingFaceDatasetClient(settings)
    query = st.text_input("Search Hugging Face datasets")
    if st.button("Search Hugging Face"):
        st.session_state.hf_results = client.search(query)
    results = st.session_state.get("hf_results", [])
    if not results:
        return
    selected = st.selectbox(
        "Hugging Face result", results, format_func=lambda item: item.dataset_id
    )
    if st.button("List dataset files"):
        st.session_state.hf_files = client.list_files(selected.dataset_id)
        st.session_state.hf_repo = selected.dataset_id
    files = st.session_state.get("hf_files", [])
    chosen = st.multiselect("Dataset files", files)
    if chosen and st.button("Download selected files"):
        repo_id = st.session_state.hf_repo
        _add_assets([client.download(repo_id, filename) for filename in chosen])


def _render_inventory() -> None:
    inventory = loaded_assets()
    st.divider()
    st.subheader("Loaded datasets")
    if not inventory:
        st.info("No datasets loaded yet.")
        return
    rows = [
        {
            "name": asset.path.name,
            "source": asset.source_kind,
            "size_mb": round(asset.size_bytes / 1_048_576, 3),
            "sha256": asset.sha256[:12],
        }
        for asset in inventory.values()
    ]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    if st.button("Clear loaded datasets"):
        inventory.clear()
        st.session_state.pop("forecast_outputs", None)
        st.rerun()
