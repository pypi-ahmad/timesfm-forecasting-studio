from __future__ import annotations

from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import pytest

from timesfm_app.manual_datasets import (
    DatasetValidationError,
    build_appliance_series,
    build_bikeshare_series,
    build_dataset_suite,
    build_fred_series,
    build_noaa_series,
    build_taxi_series,
    download_dataset_suite,
    write_dataset_files,
)


def test_build_fred_series_uses_month_start_timestamps() -> None:
    raw = pd.DataFrame(
        {"observation_date": ["2025-01-01", "2025-02-01"], "UNRATE": [4.0, 4.1]}
    )

    actual = build_fred_series(raw)

    expected = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2025-01-01", "2025-02-01"]),
            "unemployment_rate_pct": [4.0, 4.1],
        }
    )
    pd.testing.assert_frame_equal(actual, expected)


def test_build_fred_series_excludes_rows_after_the_stable_september_2025_window() -> None:
    raw = pd.DataFrame(
        {
            "observation_date": ["2025-09-01", "2025-10-01", "2025-11-01"],
            "UNRATE": [4.4, None, 4.5],
        }
    )

    actual = build_fred_series(raw)

    assert actual["timestamp"].tolist() == [pd.Timestamp("2025-09-01")]


def test_build_noaa_series_uses_date_and_maximum_temperature() -> None:
    raw = pd.DataFrame({"DATE": ["2025-01-01", "2025-01-02"], "TMAX": [3.2, 4.7]})

    actual = build_noaa_series(raw)

    assert actual.columns.tolist() == ["timestamp", "max_temperature_c"]
    assert actual["max_temperature_c"].tolist() == [3.2, 4.7]


def test_build_appliance_series_preserves_the_ten_minute_grid() -> None:
    raw = pd.DataFrame(
        {
            "date": ["2016-01-01 00:00:00", "2016-01-01 00:10:00"],
            "Appliances": [50, 60],
        }
    )

    actual = build_appliance_series(raw)

    assert actual.columns.tolist() == ["timestamp", "energy_wh"]
    assert actual["energy_wh"].tolist() == [50, 60]


def test_build_bikeshare_series_fills_missing_hours_with_zero() -> None:
    raw = pd.DataFrame(
        {
            "dteday": ["2011-01-01", "2011-01-01"],
            "hr": [0, 2],
            "cnt": [3, 5],
        }
    )

    actual = build_bikeshare_series(raw)

    assert actual["timestamp"].tolist() == list(
        pd.date_range("2011-01-01 00:00:00", periods=3, freq="h")
    )
    assert actual["rentals"].tolist() == [3, 0, 5]


def test_build_taxi_series_aggregates_and_fills_each_hour() -> None:
    raw = pd.DataFrame(
        {
            "tpep_pickup_datetime": [
                "2025-01-01 00:05:00",
                "2025-01-01 00:45:00",
                "2025-01-01 02:15:00",
            ]
        }
    )

    actual = build_taxi_series(raw)

    assert actual["timestamp"].tolist() == list(
        pd.date_range("2025-01-01 00:00:00", periods=3, freq="h")
    )
    assert actual["pickup_count"].tolist() == [2, 0, 1]


def test_builders_reject_irregular_source_timestamps() -> None:
    raw = pd.DataFrame(
        {
            "date": ["2016-01-01 00:00:00", "2016-01-01 00:20:00"],
            "Appliances": [50, 60],
        }
    )

    with pytest.raises(DatasetValidationError, match="regular"):
        build_appliance_series(raw)


def test_write_dataset_files_creates_the_manual_upload_suite(workspace_tmp_path: Path) -> None:
    series = pd.DataFrame(
        {"timestamp": pd.to_datetime(["2025-01-01", "2025-01-02"]), "value": [1, 2]}
    )

    paths = write_dataset_files(
        workspace_tmp_path,
        {
            "01_us_unemployment_monthly.csv": series,
            "02_central_park_daily_temperature.csv": series,
            "03_appliance_energy_10min.csv": series,
            "04_capital_bikeshare_hourly.xlsx": series,
            "05_nyc_yellow_taxi_hourly.parquet": series,
        },
    )

    assert [path.name for path in paths] == [
        "01_us_unemployment_monthly.csv",
        "02_central_park_daily_temperature.csv",
        "03_appliance_energy_10min.csv",
        "04_capital_bikeshare_hourly.xlsx",
        "05_nyc_yellow_taxi_hourly.parquet",
    ]
    assert pd.read_csv(paths[0])["value"].tolist() == [1, 2]
    assert pd.read_excel(paths[3], sheet_name="series")["value"].tolist() == [1, 2]
    assert pd.read_parquet(paths[4])["value"].tolist() == [1, 2]


def test_build_dataset_suite_assigns_each_manual_file_name() -> None:
    raw_sources = {
        "fred": pd.DataFrame(
            {"observation_date": ["2025-01-01", "2025-02-01"], "UNRATE": [4.0, 4.1]}
        ),
        "noaa": pd.DataFrame({"DATE": ["2025-01-01", "2025-01-02"], "TMAX": [3.2, 4.7]}),
        "appliance": pd.DataFrame(
            {
                "date": ["2016-01-01 00:00:00", "2016-01-01 00:10:00"],
                "Appliances": [50, 60],
            }
        ),
        "bikeshare": pd.DataFrame(
            {"dteday": ["2011-01-01", "2011-01-01"], "hr": [0, 1], "cnt": [3, 5]}
        ),
        "taxi": pd.DataFrame(
            {"tpep_pickup_datetime": ["2025-01-01 00:05:00", "2025-01-01 01:15:00"]}
        ),
    }

    actual = build_dataset_suite(raw_sources)

    assert list(actual) == [
        "01_us_unemployment_monthly.csv",
        "02_central_park_daily_temperature.csv",
        "03_appliance_energy_10min.csv",
        "04_capital_bikeshare_hourly.xlsx",
        "05_nyc_yellow_taxi_hourly.parquet",
    ]


def test_download_dataset_suite_writes_files_from_downloaded_payloads(
    workspace_tmp_path: Path,
) -> None:
    def zip_csv(filename: str, content: str) -> bytes:
        payload = BytesIO()
        with ZipFile(payload, "w") as archive:
            archive.writestr(filename, content)
        return payload.getvalue()

    taxi_payload = BytesIO()
    pd.DataFrame(
        {"tpep_pickup_datetime": ["2025-01-01 00:05:00", "2025-01-01 01:15:00"]}
    ).to_parquet(taxi_payload, index=False)
    payloads = iter(
        [
            b"observation_date,UNRATE\n2025-01-01,4.0\n2025-02-01,4.1\n",
            b"DATE,TMAX\n2025-01-01,3.2\n2025-01-02,4.7\n",
            zip_csv(
                "energydata_complete.csv",
                "date,Appliances\n2016-01-01 00:00:00,50\n2016-01-01 00:10:00,60\n",
            ),
            zip_csv("hour.csv", "dteday,hr,cnt\n2011-01-01,0,3\n2011-01-01,1,5\n"),
            taxi_payload.getvalue(),
        ]
    )

    paths = download_dataset_suite(workspace_tmp_path / "manual-data", lambda _: next(payloads))

    assert [path.name for path in paths] == [
        "01_us_unemployment_monthly.csv",
        "02_central_park_daily_temperature.csv",
        "03_appliance_energy_10min.csv",
        "04_capital_bikeshare_hourly.xlsx",
        "05_nyc_yellow_taxi_hourly.parquet",
    ]
