"""Stable data-loading facade for local files and public URLs."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from timesfm_app.contracts import ResolvedAsset
from timesfm_app.ingestion.readers import list_excel_sheets, read_tabular
from timesfm_app.ingestion.resolvers import cache_uploaded_file, download_public_url


@dataclass(frozen=True)
class UploadPayload:
    """Framework-neutral uploaded file payload."""

    name: str
    content: bytes


@dataclass(frozen=True)
class LoadedDataset:
    """One parsed tabular asset and its inferred datetime candidates."""

    dataset_id: str
    name: str
    asset: ResolvedAsset
    frame: pd.DataFrame
    datetime_columns: tuple[str, ...]
    sheet_name: str | None = None


def cache_uploads(uploads: Sequence[UploadPayload], cache_root: Path) -> list[ResolvedAsset]:
    """Cache every upload independently while preserving input order."""

    return [cache_uploaded_file(item.name, item.content, cache_root) for item in uploads]


def load_dataset(asset: ResolvedAsset, *, sheet_name: str | None = None) -> LoadedDataset:
    frame = read_tabular(asset.path, sheet_name=sheet_name)
    return LoadedDataset(
        dataset_id=asset.sha256,
        name=asset.path.name,
        asset=asset,
        frame=frame,
        datetime_columns=detect_datetime_columns(frame),
        sheet_name=sheet_name,
    )


def load_remote_dataset(url: str, cache_root: Path) -> LoadedDataset:
    """Download, validate, cache, and parse one public HTTP(S) dataset."""

    return load_dataset(download_public_url(url, cache_root))


def workbook_sheets(asset: ResolvedAsset) -> tuple[str, ...]:
    return tuple(list_excel_sheets(asset.path))


def detect_datetime_columns(
    frame: pd.DataFrame,
    *,
    sample_size: int = 1_000,
    minimum_parse_ratio: float = 0.8,
) -> tuple[str, ...]:
    """Rank likely datetime columns without interpreting numeric identifiers as dates."""

    scored: list[tuple[int, int, str]] = []
    name_tokens = ("date", "time", "timestamp", "datetime", "ds")
    for position, column in enumerate(frame.columns):
        series = frame[column]
        if pd.api.types.is_datetime64_any_dtype(series.dtype):
            scored.append((300, -position, str(column)))
            continue
        if pd.api.types.is_numeric_dtype(series.dtype):
            continue
        sample = series.dropna().astype("string").head(sample_size)
        if sample.empty:
            continue
        parsed = pd.to_datetime(sample, errors="coerce")
        parse_ratio = float(parsed.notna().mean())
        if parse_ratio < minimum_parse_ratio:
            continue
        normalized_name = str(column).casefold()
        name_score = 100 if any(token in normalized_name for token in name_tokens) else 0
        scored.append((200 + name_score, -position, str(column)))
    scored.sort(reverse=True)
    return tuple(column for _score, _position, column in scored)
