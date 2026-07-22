# Manual dataset suite

Create the local dataset suite from the repository root:

```powershell
uv run python scripts/download_manual_datasets.py
```

The command writes five ready-to-upload files to `manual-data/`. The directory is
gitignored; it is safe to refresh or delete locally and is never committed.

| File | Source | Select in the app | Frequency |
| --- | --- | --- | --- |
| `01_us_unemployment_monthly.csv` | [FRED UNRATE](https://fred.stlouisfed.org/series/UNRATE) | `timestamp`, `unemployment_rate_pct` | Monthly |
| `02_central_park_daily_temperature.csv` | [NOAA GHCN-D](https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily) | `timestamp`, `max_temperature_c` | Daily |
| `03_appliance_energy_10min.csv` | [UCI Appliances Energy Prediction](https://archive.ics.uci.edu/dataset/374/appliances%2Benergy%2Bprediction) | `timestamp`, `energy_wh` | 10 minutes |
| `04_capital_bikeshare_hourly.xlsx` | [UCI Bike Sharing](https://archive.ics.uci.edu/dataset/275/bike%2Bsharing%2Bdataset) | `series` sheet, `timestamp`, `rentals` | Hourly |
| `05_nyc_yellow_taxi_hourly.parquet` | [NYC TLC Yellow Taxi Trip Records](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) | `timestamp`, `pickup_count` | Hourly |

The FRED output ends in September 2025 and the NOAA output ends in December 2025,
avoiding incomplete upstream releases while keeping fixed historical ranges. The UCI
Appliances and Bike Sharing datasets are distributed under CC BY 4.0; retain the
linked attribution when sharing derived files. The NYC file is an hourly aggregate
of January 2025 pickup timestamps, with empty hours represented as zero pickups.

For a quick smoke test, use context length 512 and horizon 128 for the hourly and
10-minute series, and context length 120 with horizon 12 for the monthly series.
