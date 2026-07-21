from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from huggingface_hub import HfApi, hf_hub_download

from timesfm_app.contracts import SUPPORTED_SUFFIXES, ResolvedAsset


class ProviderResolutionError(ValueError):
    """Raised when a dataset provider cannot yield a supported file."""


def resolve_kaggle_dataset(
    handle: str,
    *,
    path: str | None = None,
    downloader: Callable[..., str] | None = None,
) -> list[ResolvedAsset]:
    if not handle.strip() or "/" not in handle:
        raise ProviderResolutionError("Kaggle handle must use owner/dataset format.")
    if downloader is None:
        import kagglehub

        downloader = kagglehub.dataset_download

    resolved = Path(downloader(handle, path=path))
    candidates = [resolved] if resolved.is_file() else sorted(resolved.rglob("*"))
    supported = [candidate for candidate in candidates if _is_supported_file(candidate)]
    if not supported:
        raise ProviderResolutionError("Kaggle dataset contains no supported tabular files.")

    revision_match = re.search(r"/versions/(\d+)$", handle.rstrip("/"))
    revision = revision_match.group(1) if revision_match else None
    return [
        _existing_asset(candidate, "kaggle", handle, revision=revision) for candidate in supported
    ]


def list_huggingface_files(
    repo_id: str,
    *,
    revision: str | None = None,
    token: str | None = None,
    api: Any | None = None,
) -> list[str]:
    active_api = api or HfApi(token=token)
    files = active_api.list_repo_files(
        repo_id=repo_id,
        repo_type="dataset",
        revision=revision,
        token=token,
    )
    return sorted(file for file in files if Path(file).suffix.lower() in SUPPORTED_SUFFIXES)


def resolve_huggingface_file(
    repo_id: str,
    filename: str,
    cache_root: Path,
    *,
    revision: str | None = None,
    token: str | None = None,
    offline: bool = False,
    api: Any | None = None,
    downloader: Callable[..., str] = hf_hub_download,
) -> ResolvedAsset:
    if Path(filename).suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ProviderResolutionError("Selected Hugging Face file format is unsupported.")

    active_api = api or HfApi(token=token)
    try:
        resolved_revision = revision
        if not offline:
            resolved_revision = active_api.repo_info(
                repo_id=repo_id,
                repo_type="dataset",
                revision=revision,
                token=token,
            ).sha
        local_path = Path(
            downloader(
                repo_id=repo_id,
                filename=filename,
                repo_type="dataset",
                revision=resolved_revision,
                cache_dir=str(cache_root),
                token=token,
                local_files_only=offline,
            )
        )
    except Exception as error:
        raise ProviderResolutionError(f"Hugging Face dataset download failed: {error}") from error

    locator = f"hf://datasets/{repo_id}/{filename}"
    return _existing_asset(
        local_path,
        "huggingface",
        locator,
        revision=resolved_revision,
    )


def _is_supported_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES


def _existing_asset(
    path: Path,
    source_kind: str,
    locator: str,
    *,
    revision: str | None = None,
) -> ResolvedAsset:
    hasher = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            hasher.update(chunk)
    return ResolvedAsset(
        path=path,
        source_kind=source_kind,
        locator=locator,
        sha256=hasher.hexdigest(),
        size_bytes=path.stat().st_size,
        revision=revision,
    )
