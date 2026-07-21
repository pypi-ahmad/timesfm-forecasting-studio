from __future__ import annotations

import hashlib
from pathlib import Path

import httpx
import pandas as pd
import pytest

from timesfm_app.ingestion.readers import list_excel_sheets, read_tabular
from timesfm_app.ingestion.resolvers import (
    SourceResolutionError,
    cache_uploaded_file,
    download_public_url,
    validate_public_url,
)


@pytest.mark.parametrize("suffix", [".csv", ".parquet"])
def test_read_tabular_reads_supported_columnar_formats(
    workspace_tmp_path: Path, suffix: str
) -> None:
    expected = pd.DataFrame({"ds": ["2026-01-01"], "y": [12.5]})
    path = workspace_tmp_path / f"series{suffix}"
    if suffix == ".csv":
        expected.to_csv(path, index=False)
    else:
        expected.to_parquet(path, index=False)

    actual = read_tabular(path)

    pd.testing.assert_frame_equal(actual, expected)


def test_read_tabular_selects_excel_sheet(workspace_tmp_path: Path) -> None:
    path = workspace_tmp_path / "series.xlsx"
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame({"value": [1]}).to_excel(writer, sheet_name="first", index=False)
        pd.DataFrame({"value": [2]}).to_excel(writer, sheet_name="second", index=False)

    assert list_excel_sheets(path) == ["first", "second"]
    actual = read_tabular(path, sheet_name="second")

    assert actual["value"].tolist() == [2]


def test_cache_uploaded_file_uses_content_hash(workspace_tmp_path: Path) -> None:
    content = b"ds,y\n2026-01-01,1\n"

    asset = cache_uploaded_file("series.csv", content, workspace_tmp_path)

    assert asset.path.read_bytes() == content
    assert asset.sha256 == hashlib.sha256(content).hexdigest()
    assert asset.path.name == "series.csv"


def test_cache_uploaded_file_rejects_unsupported_extension(workspace_tmp_path: Path) -> None:
    with pytest.raises(SourceResolutionError, match="Unsupported"):
        cache_uploaded_file("series.zip", b"data", workspace_tmp_path)


@pytest.mark.parametrize(
    "url,addresses,error",
    [
        ("file:///tmp/data.csv", [], "HTTP"),
        ("https://user:secret@example.com/data.csv", ["93.184.216.34"], "credentials"),
        ("https://localhost/data.csv", ["127.0.0.1"], "private"),
        ("https://metadata/data.csv", ["169.254.169.254"], "private"),
    ],
)
def test_validate_public_url_rejects_unsafe_targets(
    url: str, addresses: list[str], error: str
) -> None:
    with pytest.raises(SourceResolutionError, match=error):
        validate_public_url(url, host_resolver=lambda _: addresses)


def test_download_public_url_streams_supported_file_to_cache(workspace_tmp_path: Path) -> None:
    content = b"ds,y\n2026-01-01,1\n"
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={"content-type": "text/csv", "content-length": str(len(content))},
            content=content,
            request=request,
        )
    )

    with httpx.Client(transport=transport) as client:
        asset = download_public_url(
            "https://example.com/series.csv",
            workspace_tmp_path,
            client=client,
            host_resolver=lambda _: ["93.184.216.34"],
        )

    assert asset.path.read_bytes() == content
    assert asset.source_kind == "url"
    assert asset.locator == "https://example.com/series.csv"


def test_download_public_url_does_not_retain_query_secrets(workspace_tmp_path: Path) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"ds,y\n2026-01-01,1\n", request=request)
    )

    with httpx.Client(transport=transport) as client:
        asset = download_public_url(
            "https://example.com/series.csv?token=secret",
            workspace_tmp_path,
            client=client,
            host_resolver=lambda _: ["93.184.216.34"],
        )

    assert asset.locator == "https://example.com/series.csv"


def test_download_public_url_enforces_size_limit(workspace_tmp_path: Path) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            headers={"content-type": "text/csv", "content-length": "100"},
            content=b"x" * 100,
            request=request,
        )
    )

    with (
        httpx.Client(transport=transport) as client,
        pytest.raises(SourceResolutionError, match="size limit"),
    ):
        download_public_url(
            "https://example.com/series.csv",
            workspace_tmp_path,
            client=client,
            max_bytes=10,
            host_resolver=lambda _: ["93.184.216.34"],
        )
