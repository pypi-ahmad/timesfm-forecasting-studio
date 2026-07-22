"""Normalize public time-series sources into files accepted by the app."""

from __future__ import annotations

from collections.abc import Callable
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd

FRED_UNEMPLOYMENT_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=UNRATE"
FRED_UNEMPLOYMENT_END_DATE = pd.Timestamp("2025-09-01")
NOAA_CENTRAL_PARK_URL = (
    "https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries"
    "&stations=USW00094728&startDate=2016-01-01&endDate=2025-12-31"
    "&format=csv&includeAttributes=false&units=metric"
)
UCI_APPLIANCES_URL = "https://archive.ics.uci.edu/static/public/374/appliances+energy+prediction.zip"
UCI_BIKESHARE_URL = "https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip"
NYC_TAXI_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet"


class DatasetValidationError(ValueError):
    """Raised when a downloaded dataset cannot form a valid forecast series."""


def build_fred_series(raw: pd.DataFrame) -> pd.DataFrame:
    """Return the FRED unemployment-rate series on its monthly grid."""

    _require_columns(raw, ("observation_date", "UNRATE"))
    dates = pd.to_datetime(raw["observation_date"], errors="coerce")
    return _regular_series(
        raw.loc[dates <= FRED_UNEMPLOYMENT_END_DATE],
        timestamp_column="observation_date",
        target_column="UNRATE",
        output_target="unemployment_rate_pct",
        frequency="MS",
    )


def build_noaa_series(raw: pd.DataFrame) -> pd.DataFrame:
    """Return daily Central Park maximum temperatures."""

    return _regular_series(
        raw,
        timestamp_column="DATE",
        target_column="TMAX",
        output_target="max_temperature_c",
        frequency="D",
    )


def build_appliance_series(raw: pd.DataFrame) -> pd.DataFrame:
    """Return the 10-minute appliance energy-use series."""

    return _regular_series(
        raw,
        timestamp_column="date",
        target_column="Appliances",
        output_target="energy_wh",
        frequency="10min",
    )


def build_bikeshare_series(raw: pd.DataFrame) -> pd.DataFrame:
    """Return Capital Bikeshare counts, filling omitted hours with zero rentals."""

    _require_columns(raw, ("dteday", "hr", "cnt"))
    timestamp = pd.to_datetime(raw["dteday"], errors="coerce") + pd.to_timedelta(
        pd.to_numeric(raw["hr"], errors="coerce"), unit="h"
    )
    values = pd.to_numeric(raw["cnt"], errors="coerce")
    frame = pd.DataFrame({"timestamp": timestamp, "rentals": values})
    _validate_timestamp_and_values(frame, "timestamp", "rentals")
    if frame["timestamp"].duplicated().any():
        raise DatasetValidationError("Bike-share timestamps must be unique.")

    complete = (
        frame.set_index("timestamp")
        .sort_index()
        .reindex(pd.date_range(frame["timestamp"].min(), frame["timestamp"].max(), freq="h"))
        .fillna({"rentals": 0})
        .rename_axis("timestamp")
        .reset_index()
    )
    return _regular_series(
        complete,
        timestamp_column="timestamp",
        target_column="rentals",
        output_target="rentals",
        frequency="h",
    )


def build_taxi_series(raw: pd.DataFrame) -> pd.DataFrame:
    """Aggregate NYC Yellow Taxi pickups into a complete hourly count series."""

    _require_columns(raw, ("tpep_pickup_datetime",))
    timestamps = pd.to_datetime(raw["tpep_pickup_datetime"], errors="coerce")
    if timestamps.isna().any():
        raise DatasetValidationError("Taxi pickup timestamps must all be valid datetimes.")

    counts = timestamps.dt.floor("h").value_counts().sort_index().rename("pickup_count")
    complete = (
        counts.reindex(
            pd.date_range(counts.index.min(), counts.index.max(), freq="h"), fill_value=0
        )
        .rename_axis("timestamp")
        .reset_index()
    )
    return _regular_series(
        complete,
        timestamp_column="timestamp",
        target_column="pickup_count",
        output_target="pickup_count",
        frequency="h",
    )


def build_dataset_suite(raw_sources: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Build every local manual-testing dataset from its raw source frame."""

    required = ("fred", "noaa", "appliance", "bikeshare", "taxi")
    missing = [name for name in required if name not in raw_sources]
    if missing:
        raise DatasetValidationError(f"Missing raw source datasets: {', '.join(missing)}.")
    return {
        "01_us_unemployment_monthly.csv": build_fred_series(raw_sources["fred"]),
        "02_central_park_daily_temperature.csv": build_noaa_series(raw_sources["noaa"]),
        "03_appliance_energy_10min.csv": build_appliance_series(raw_sources["appliance"]),
        "04_capital_bikeshare_hourly.xlsx": build_bikeshare_series(raw_sources["bikeshare"]),
        "05_nyc_yellow_taxi_hourly.parquet": build_taxi_series(raw_sources["taxi"]),
    }


def download_dataset_suite(output_dir: Path, fetch_bytes: Callable[[str], bytes]) -> list[Path]:
    """Download the five public sources and write ready-to-upload app files."""

    raw_sources = {
        "fred": pd.read_csv(BytesIO(fetch_bytes(FRED_UNEMPLOYMENT_URL))),
        "noaa": pd.read_csv(BytesIO(fetch_bytes(NOAA_CENTRAL_PARK_URL))),
        "appliance": _read_zip_csv(
            fetch_bytes(UCI_APPLIANCES_URL), "energydata_complete.csv"
        ),
        "bikeshare": _read_zip_csv(fetch_bytes(UCI_BIKESHARE_URL), "hour.csv"),
        "taxi": pd.read_parquet(BytesIO(fetch_bytes(NYC_TAXI_URL))),
    }
    return write_dataset_files(output_dir, build_dataset_suite(raw_sources))


def write_dataset_files(output_dir: Path, datasets: dict[str, pd.DataFrame]) -> list[Path]:
    """Write normalized datasets in the formats accepted by the application."""

    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for filename, frame in datasets.items():
        path = output_dir / filename
        if path.suffix == ".csv":
            frame.to_csv(path, index=False)
        elif path.suffix == ".xlsx":
            with pd.ExcelWriter(path) as writer:
                frame.to_excel(writer, sheet_name="series", index=False)
        elif path.suffix == ".parquet":
            frame.to_parquet(path, index=False)
        else:
            raise DatasetValidationError(f"Unsupported output format: {path.suffix or '<none>'}")
        paths.append(path)
    return paths


def _read_zip_csv(payload: bytes, filename: str) -> pd.DataFrame:
    with ZipFile(BytesIO(payload)) as archive:
        try:
            with archive.open(filename) as source:
                return pd.read_csv(source)
        except KeyError as error:
            raise DatasetValidationError(f"Archive does not contain {filename}.") from error


def _regular_series(
    raw: pd.DataFrame,
    *,
    timestamp_column: str,
    target_column: str,
    output_target: str,
    frequency: str,
) -> pd.DataFrame:
    _require_columns(raw, (timestamp_column, target_column))
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(raw[timestamp_column], errors="coerce"),
            output_target: pd.to_numeric(raw[target_column], errors="coerce"),
        }
    )
    _validate_timestamp_and_values(frame, "timestamp", output_target)
    frame = frame.sort_values("timestamp", kind="stable").reset_index(drop=True)
    if frame["timestamp"].duplicated().any():
        raise DatasetValidationError("Timestamps must be unique.")

    expected = pd.date_range(
        frame["timestamp"].iloc[0], frame["timestamp"].iloc[-1], freq=frequency
    )
    if not frame["timestamp"].equals(pd.Series(expected, name="timestamp")):
        raise DatasetValidationError(f"Timestamps must form a regular {frequency} grid.")
    return frame


def _require_columns(raw: pd.DataFrame, columns: tuple[str, ...]) -> None:
    missing = [column for column in columns if column not in raw.columns]
    if missing:
        raise DatasetValidationError(f"Dataset is missing required columns: {', '.join(missing)}.")


def _validate_timestamp_and_values(
    frame: pd.DataFrame, timestamp_column: str, target_column: str
) -> None:
    if frame.empty:
        raise DatasetValidationError("Dataset must contain at least one row.")
    if frame[timestamp_column].isna().any():
        raise DatasetValidationError("Timestamps must all be valid datetimes.")
    values = frame[target_column].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise DatasetValidationError("Target values must all be finite numbers.")
