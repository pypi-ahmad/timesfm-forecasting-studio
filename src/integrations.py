"""Stable search and download clients for supported dataset providers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal

from huggingface_hub import HfApi

from timesfm_app.config import AppSettings
from timesfm_app.contracts import ResolvedAsset
from timesfm_app.ingestion.providers import (
    list_huggingface_files,
    resolve_huggingface_file,
    resolve_kaggle_dataset,
)


class IntegrationError(RuntimeError):
    """Raised when a provider cannot search or resolve a dataset."""


@dataclass(frozen=True)
class DatasetSearchResult:
    provider: Literal["kaggle", "huggingface"]
    dataset_id: str
    title: str
    description: str = ""


class KaggleDatasetClient:
    def __init__(self, settings: AppSettings, *, api: Any | None = None) -> None:
        self.settings = settings
        self._api = api

    @property
    def is_configured(self) -> bool:
        return bool(
            self.settings.kaggle_api_token
            or (self.settings.kaggle_username and self.settings.kaggle_key)
        )

    def search(self, query: str, *, limit: int = 20) -> list[DatasetSearchResult]:
        if not self.is_configured:
            raise IntegrationError("Kaggle credentials are not configured.")
        if len(query.strip()) < 2:
            raise IntegrationError("Enter at least two characters to search Kaggle.")
        try:
            api = self._api or self._create_api()
            api.authenticate()
            raw_results = api.dataset_list(search=query.strip(), page=1) or []
            return [self._normalize(item) for item in raw_results if item is not None][:limit]
        except IntegrationError:
            raise
        except Exception as error:
            raise IntegrationError(
                f"Kaggle search failed ({type(error).__name__}); "
                "verify credentials and network access."
            ) from error

    def download(self, dataset_id: str, *, path: str | None = None) -> list[ResolvedAsset]:
        try:
            return resolve_kaggle_dataset(dataset_id, path=path)
        except Exception as error:
            raise IntegrationError(f"Kaggle download failed ({type(error).__name__}).") from error

    def _create_api(self) -> Any:
        if self.settings.kaggle_api_token:
            os.environ.setdefault("KAGGLE_API_TOKEN", self.settings.kaggle_api_token)
        if self.settings.kaggle_username:
            os.environ.setdefault("KAGGLE_USERNAME", self.settings.kaggle_username)
        if self.settings.kaggle_key:
            os.environ.setdefault("KAGGLE_KEY", self.settings.kaggle_key)
        from kaggle.api.kaggle_api_extended import KaggleApi

        return KaggleApi()

    @staticmethod
    def _normalize(item: Any) -> DatasetSearchResult:
        dataset_id = str(getattr(item, "ref", "")).strip()
        if "/" not in dataset_id:
            raise IntegrationError("Kaggle returned an invalid dataset identifier.")
        return DatasetSearchResult(
            provider="kaggle",
            dataset_id=dataset_id,
            title=str(getattr(item, "title", dataset_id) or dataset_id),
            description=str(getattr(item, "subtitle", "") or ""),
        )


class HuggingFaceDatasetClient:
    def __init__(self, settings: AppSettings, *, api: Any | None = None) -> None:
        self.settings = settings
        self._api = api or HfApi(token=settings.hf_token)

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.hf_token)

    def search(self, query: str, *, limit: int = 20) -> list[DatasetSearchResult]:
        if len(query.strip()) < 2:
            raise IntegrationError("Enter at least two characters to search Hugging Face.")
        try:
            raw_results = self._api.list_datasets(
                search=query.strip(), limit=limit, token=self.settings.hf_token
            )
            return [self._normalize(item) for item in raw_results]
        except Exception as error:
            raise IntegrationError(
                f"Hugging Face search failed ({type(error).__name__}); verify network access."
            ) from error

    def list_files(self, dataset_id: str, *, revision: str | None = None) -> list[str]:
        return list_huggingface_files(
            dataset_id,
            revision=revision,
            token=self.settings.hf_token,
            api=self._api,
        )

    def download(
        self, dataset_id: str, filename: str, *, revision: str | None = None
    ) -> ResolvedAsset:
        return resolve_huggingface_file(
            dataset_id,
            filename,
            self.settings.data_cache / "huggingface",
            revision=revision,
            token=self.settings.hf_token,
            offline=self.settings.offline,
            api=self._api,
        )

    @staticmethod
    def _normalize(item: Any) -> DatasetSearchResult:
        dataset_id = str(getattr(item, "id", "")).strip()
        if "/" not in dataset_id:
            raise IntegrationError("Hugging Face returned an invalid dataset identifier.")
        return DatasetSearchResult(
            provider="huggingface",
            dataset_id=dataset_id,
            title=dataset_id,
            description=str(getattr(item, "description", "") or ""),
        )
