"""Download five ready-to-upload datasets for local manual app testing."""

from pathlib import Path

import httpx

from timesfm_app.manual_datasets import download_dataset_suite

with httpx.Client(follow_redirects=True, timeout=120) as client:
    paths = download_dataset_suite(
        Path("manual-data"), lambda url: client.get(url).raise_for_status().content
    )

for path in paths:
    print(path)
