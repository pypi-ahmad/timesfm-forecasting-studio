from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from timesfm_app.ingestion.providers import (
    ProviderResolutionError,
    list_huggingface_files,
    resolve_huggingface_file,
    resolve_kaggle_dataset,
)


def test_resolve_kaggle_dataset_returns_supported_files(workspace_tmp_path: Path) -> None:
    dataset_dir = workspace_tmp_path / "download"
    dataset_dir.mkdir(exist_ok=True)
    (dataset_dir / "series.csv").write_text("ds,y\n2026-01-01,1\n", encoding="utf-8")
    (dataset_dir / "notes.txt").write_text("ignore", encoding="utf-8")
    calls: list[tuple[str, str | None]] = []

    def downloader(handle: str, path: str | None = None) -> str:
        calls.append((handle, path))
        return str(dataset_dir)

    assets = resolve_kaggle_dataset("owner/dataset/versions/3", downloader=downloader)

    assert calls == [("owner/dataset/versions/3", None)]
    assert [asset.path.name for asset in assets] == ["series.csv"]
    assert assets[0].revision == "3"


def test_resolve_kaggle_dataset_requires_supported_file(workspace_tmp_path: Path) -> None:
    dataset_dir = workspace_tmp_path / "empty"
    dataset_dir.mkdir(exist_ok=True)
    (dataset_dir / "notes.txt").write_text("ignore", encoding="utf-8")

    with pytest.raises(ProviderResolutionError, match="supported"):
        resolve_kaggle_dataset(
            "owner/dataset", downloader=lambda *_args, **_kwargs: str(dataset_dir)
        )


def test_list_huggingface_files_filters_supported_formats() -> None:
    class FakeApi:
        def list_repo_files(self, **_kwargs: object) -> list[str]:
            return ["README.md", "data/train.csv", "data/test.parquet", "archive.zip"]

    files = list_huggingface_files("owner/dataset", api=FakeApi())

    assert files == ["data/test.parquet", "data/train.csv"]


def test_resolve_huggingface_file_pins_resolved_revision(workspace_tmp_path: Path) -> None:
    source = workspace_tmp_path / "source.csv"
    source.write_text("ds,y\n2026-01-01,1\n", encoding="utf-8")
    calls: list[dict[str, object]] = []

    class FakeApi:
        def repo_info(self, **_kwargs: object) -> SimpleNamespace:
            return SimpleNamespace(sha="deadbeef")

    def downloader(**kwargs: object) -> str:
        calls.append(kwargs)
        return str(source)

    asset = resolve_huggingface_file(
        "owner/dataset",
        "data.csv",
        workspace_tmp_path / "hf-cache",
        api=FakeApi(),
        downloader=downloader,
        token="secret-token",
    )

    assert asset.revision == "deadbeef"
    assert calls[0]["revision"] == "deadbeef"
    assert calls[0]["repo_type"] == "dataset"
    assert "secret-token" not in asset.locator
