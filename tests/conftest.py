from __future__ import annotations

import re
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

_TEMP_ROOT = (Path("tests/.runtime") / "python-temp").resolve()
_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(_TEMP_ROOT)


def _workspace_mkdtemp(suffix: str = "", prefix: str | None = None, dir: str | None = None) -> str:
    root = Path(dir or tempfile.gettempdir())
    stem = prefix or "tmp"
    for _ in range(100):
        path = root / f"{stem}{uuid4().hex}{suffix}"
        try:
            path.mkdir(mode=0o777)
        except FileExistsError:
            continue
        return str(path)
    raise FileExistsError("Could not create unique workspace temporary directory.")


tempfile.mkdtemp = _workspace_mkdtemp


@pytest.fixture
def workspace_tmp_path(request: pytest.FixtureRequest) -> Path:
    safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", request.node.name)
    path = Path("tests/.runtime") / safe_name
    path.mkdir(parents=True, exist_ok=True)
    return path
