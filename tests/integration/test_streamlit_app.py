from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_app_renders_batch_workflows_without_loading_model() -> None:
    app_path = Path(__file__).parents[2] / "app.py"
    app = AppTest.from_file(app_path, default_timeout=10).run()

    assert not app.exception
    assert app.title[0].value == "TimesFM Forecast Studio"
    assert app.segmented_control[0].label == "Workflow stage"
    assert app.segmented_control[0].options == [
        "Load & configure",
        "Analyze",
        "Forecast",
        "Evaluate & anomalies",
        "Export",
    ]
    assert any(select.label == "Compute device" for select in app.selectbox)
    assert any(number.label == "Context length" for number in app.number_input)
    assert any(number.label == "Forecast horizon" for number in app.number_input)
    assert app.radio[0].label == "Data source"
    assert app.file_uploader[0].label == "Upload datasets"
    assert any(toggle.label == "Manual simulator" for toggle in app.toggle)


def test_app_accepts_multiple_uploads_and_renders_per_file_mappings() -> None:
    app_path = Path(__file__).parents[2] / "app.py"
    app = AppTest.from_file(app_path, default_timeout=10).run()

    app.file_uploader[0].set_value(
        [
            ("daily.csv", b"date,value\n2026-01-01,1\n2026-01-02,2\n", "text/csv"),
            ("hourly.csv", b"time,demand\n2026-01-01 00:00,3\n2026-01-01 01:00,4\n", "text/csv"),
        ]
    ).run()
    app.segmented_control[0].set_value("Forecast").run()

    assert not app.exception
    assert {expander.label for expander in app.expander} >= {"daily.csv", "hourly.csv"}
    assert sum(select.label == "Date/time column" for select in app.selectbox) == 2
    assert sum(select.label == "Target column" for select in app.selectbox) == 2


def test_clear_loaded_datasets_removes_uploads_and_generated_state() -> None:
    app_path = Path(__file__).parents[2] / "app.py"
    app = AppTest.from_file(app_path, default_timeout=10).run()
    app.file_uploader[0].set_value(
        [("daily.csv", b"date,value\n2026-01-01,1\n2026-01-02,2\n", "text/csv")]
    ).run()
    app.session_state["forecast_outputs"] = {"stale": object()}

    next(button for button in app.button if button.label == "Clear loaded datasets").click().run()

    assert not app.exception
    assert "No datasets loaded yet." in [info.value for info in app.info]
    assert "forecast_outputs" not in app.session_state
