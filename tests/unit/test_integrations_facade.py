from __future__ import annotations

from types import SimpleNamespace

import pytest

from integrations import HuggingFaceDatasetClient, IntegrationError, KaggleDatasetClient
from timesfm_app.config import AppSettings


def test_kaggle_search_normalizes_official_api_results() -> None:
    class FakeKaggleApi:
        def authenticate(self) -> None:
            pass

        def dataset_list(self, *, search: str, page: int):
            assert (search, page) == ("traffic", 1)
            return [
                SimpleNamespace(ref="owner/traffic", title="City traffic", subtitle="Hourly"),
                None,
            ]

    client = KaggleDatasetClient(AppSettings(kaggle_api_token="configured"), api=FakeKaggleApi())

    results = client.search("traffic")

    assert results[0].dataset_id == "owner/traffic"
    assert results[0].provider == "kaggle"
    assert results[0].description == "Hourly"


def test_kaggle_search_requires_configured_credentials() -> None:
    client = KaggleDatasetClient(AppSettings(), api=object())

    with pytest.raises(IntegrationError, match="credentials"):
        client.search("traffic")


def test_huggingface_search_supports_public_datasets_without_token() -> None:
    class FakeHfApi:
        def list_datasets(self, **kwargs: object):
            assert kwargs["search"] == "weather"
            assert kwargs["limit"] == 10
            return [SimpleNamespace(id="owner/weather", description="Daily weather")]

    client = HuggingFaceDatasetClient(AppSettings(), api=FakeHfApi())

    results = client.search("weather", limit=10)

    assert results[0].dataset_id == "owner/weather"
    assert results[0].title == "owner/weather"
    assert results[0].provider == "huggingface"
