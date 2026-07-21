from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_app_renders_batch_workflows_without_loading_model() -> None:
    app_path = Path(__file__).parents[2] / "app.py"
    app = AppTest.from_file(app_path, default_timeout=10).run()

    assert not app.exception
    assert app.title[0].value == "TimesFM Forecast Studio"
    assert [tab.label for tab in app.tabs[:3]] == [
        "Data Loading",
        "Interactive Forecasting Charts",
        "Manual Simulator",
    ]
    assert any(select.label == "Compute device" for select in app.selectbox)
    assert any(number.label == "Context length" for number in app.number_input)
    assert any(number.label == "Forecast horizon" for number in app.number_input)
    assert app.radio[0].label == "Data source"
    assert app.file_uploader[0].label == "Upload datasets"
    assert any(area.label == "Historical values" for area in app.text_area)
    assert any(button.label == "Forecast values" for button in app.button)


def test_app_accepts_multiple_uploads_and_renders_per_file_mappings() -> None:
    app_path = Path(__file__).parents[2] / "app.py"
    app = AppTest.from_file(app_path, default_timeout=10).run()

    app.file_uploader[0].set_value(
        [
            ("daily.csv", b"date,value\n2026-01-01,1\n2026-01-02,2\n", "text/csv"),
            ("hourly.csv", b"time,demand\n2026-01-01 00:00,3\n2026-01-01 01:00,4\n", "text/csv"),
        ]
    ).run()

    assert not app.exception
    assert {expander.label for expander in app.expander} >= {"daily.csv", "hourly.csv"}
    assert sum(select.label == "Date/time column" for select in app.selectbox) == 2
    assert sum(select.label == "Target column" for select in app.selectbox) == 2
