from timesfm_app.ui.state import clear_dataset_state


def test_clear_dataset_state_removes_loaded_data_results_and_rotates_uploader() -> None:
    state = {
        "loaded_assets": {"asset": object()},
        "forecast_outputs": {"asset": object()},
        "forecast_errors": {"asset": "failure"},
        "forecast_histories": {"asset": object()},
        "eda_result": object(),
        "backtest_result": object(),
        "anomaly_result": object(),
        "report_bundle": object(),
        "upload_generation": 4,
        "unrelated_preference": "keep",
    }

    clear_dataset_state(state)

    assert state["loaded_assets"] == {}
    assert state["upload_generation"] == 5
    assert state["unrelated_preference"] == "keep"
    for key in (
        "forecast_outputs",
        "forecast_errors",
        "forecast_histories",
        "eda_result",
        "backtest_result",
        "anomaly_result",
        "report_bundle",
    ):
        assert key not in state


def test_clear_dataset_state_initializes_missing_uploader_generation() -> None:
    state: dict[str, object] = {}

    clear_dataset_state(state)

    assert state == {"loaded_assets": {}, "upload_generation": 1}
