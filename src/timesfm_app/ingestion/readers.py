from __future__ import annotations

from pathlib import Path

import pandas as pd

from timesfm_app.contracts import SUPPORTED_SUFFIXES


def read_tabular(path: Path, *, sheet_name: str | None = None) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(f"Unsupported tabular format: {suffix or '<none>'}")
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_excel(path, sheet_name=sheet_name or 0)


def list_excel_sheets(path: Path) -> list[str]:
    if path.suffix.lower() != ".xlsx":
        return []
    with pd.ExcelFile(path) as workbook:
        return workbook.sheet_names
