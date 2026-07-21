from __future__ import annotations

from pathlib import Path

import pandas as pd

from loader import UploadPayload, cache_uploads, detect_datetime_columns, load_dataset


def test_cache_uploads_preserves_multiple_files(workspace_tmp_path: Path) -> None:
    uploads = [
        UploadPayload("daily.csv", b"date,value\n2026-01-01,1\n"),
        UploadPayload("hourly.csv", b"timestamp,value\n2026-01-01 01:00,2\n"),
    ]

    assets = cache_uploads(uploads, workspace_tmp_path)

    assert [asset.path.name for asset in assets] == ["daily.csv", "hourly.csv"]
    assert all(asset.path.exists() for asset in assets)


def test_detect_datetime_columns_ranks_native_and_named_columns() -> None:
    frame = pd.DataFrame(
        {
            "event_time": pd.date_range("2026-01-01", periods=3, freq="h"),
            "date_label": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "identifier": [20260101, 20260102, 20260103],
            "value": [1.0, 2.0, 3.0],
        }
    )

    candidates = detect_datetime_columns(frame)

    assert candidates == ("event_time", "date_label")


def test_load_dataset_exposes_frame_and_datetime_candidates(workspace_tmp_path: Path) -> None:
    assets = cache_uploads(
        [UploadPayload("series.csv", b"ds,y\n2026-01-01,1\n2026-01-02,2\n")],
        workspace_tmp_path,
    )

    dataset = load_dataset(assets[0])

    assert dataset.dataset_id == assets[0].sha256
    assert dataset.name == "series.csv"
    assert dataset.datetime_columns == ("ds",)
    assert dataset.frame["y"].tolist() == [1, 2]
