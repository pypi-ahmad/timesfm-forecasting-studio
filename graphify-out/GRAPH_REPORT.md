# Graph Report - .  (2026-07-21)

## Corpus Check
- 65 files · ~100,089 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 372 nodes · 900 edges · 25 communities (14 shown, 11 thin omitted)
- Extraction: 77% EXTRACTED · 23% INFERRED · 0% AMBIGUOUS · INFERRED: 203 edges (avg confidence: 0.71)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Data Loading & UI Pages
- Prediction & Forecast Runtime
- Slide Generation Tool
- Dataset Integrations & Config
- TimesFM Concepts & Tutorial
- Series Preprocessing & Contracts
- Ingestion Safety & Resolvers
- Provider File Resolution
- Desktop Install Docs
- HTML Validation Tooling
- Tutorial Docs & README
- Test Fixtures
- Contribution Governance
- CI & Dependencies
- Security & Support Policy
- Forecasting Package Init
- Ingestion Package Init
- App Package Init
- UI Package Init
- Dependabot Actions Config
- Documentation Issue Template
- Feature Request Template
- Package Root

## God Nodes (most connected - your core abstractions)
1. `AppSettings` - 42 edges
2. `ForecastRequest` - 29 edges
3. `ResolvedAsset` - 27 edges
4. `TimesFMRuntime` - 22 edges
5. `create_studio_slide()` - 19 edges
6. `add_text()` - 17 edges
7. `prepare_series()` - 17 edges
8. `download_public_url()` - 17 edges
9. `create_pitfalls_slide()` - 16 edges
10. `create_ingestion_slide()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `test_forecast_request_calculates_compile_buckets()` --calls--> `ForecastRequest`  [INFERRED]
  tests/unit/test_preprocessing.py → src/timesfm_app/contracts.py
- `test_forecast_request_rejects_combined_limit()` --calls--> `ForecastRequest`  [INFERRED]
  tests/unit/test_preprocessing.py → src/timesfm_app/contracts.py
- `test_detect_datetime_columns_ranks_native_and_named_columns()` --calls--> `detect_datetime_columns()`  [INFERRED]
  tests/unit/test_loader_facade.py → src/loader.py
- `test_resolve_device_supports_auto_cpu_and_cuda()` --calls--> `resolve_device()`  [INFERRED]
  tests/unit/test_predictor_facade.py → src/predictor.py
- `FakeConfig` --uses--> `AppSettings`  [INFERRED]
  tests/unit/test_forecasting.py → src/timesfm_app/config.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Zero to Master Curriculum** — docs_tutorial_01_timesfm_intro_foundations, docs_tutorial_02_local_installation_local_installation, docs_tutorial_03_data_engineering_regular_series, docs_tutorial_04_forecasting_mastery_forecasting_mastery, index_zero_to_master_tutorial [EXTRACTED 1.00]
- **TimesFM Model Mechanism** — _playwright_mcp_page_2026_07_21t15_53_03_518z_timesfm_2_5, _playwright_mcp_page_2026_07_21t15_53_03_518z_patching, _playwright_mcp_page_2026_07_21t15_53_03_518z_patched_decoder_only, _playwright_mcp_page_2026_07_21t15_53_03_518z_zero_shot_inference, _playwright_mcp_page_2026_07_21t15_53_03_518z_quantile_forecast [EXTRACTED 0.90]
- **Forecasting Approach Comparison** — _playwright_mcp_page_2026_07_21t15_53_03_518z_arima, _playwright_mcp_page_2026_07_21t15_53_03_518z_prophet, _playwright_mcp_page_2026_07_21t15_53_03_518z_deepar, _playwright_mcp_page_2026_07_21t15_53_03_518z_timesfm_2_5 [EXTRACTED 0.90]
- **Data Ingestion Pipeline** — _playwright_mcp_page_2026_07_21t15_53_03_518z_ingestion_architecture, _playwright_mcp_page_2026_07_21t15_53_03_518z_pandas_dataframe_contract, _playwright_mcp_page_2026_07_21t15_53_03_518z_remote_url_trust_boundary, _playwright_mcp_page_2026_07_21t15_53_03_518z_datetime_detection [EXTRACTED 0.90]

## Communities (25 total, 11 thin omitted)

### Community 0 - "Data Loading & UI Pages"
Cohesion: 0.07
Nodes (45): Figure, cache_uploads(), detect_datetime_columns(), load_dataset(), load_remote_dataset(), LoadedDataset, DataFrame, Path (+37 more)

### Community 1 - "Prediction & Forecast Runtime"
Cohesion: 0.09
Nodes (37): BatchPrediction, DeviceSelectionError, PredictionOutput, DeviceChoice, ValueError, Pandas-oriented TimesFM predictor facade., Raised when a requested compute device cannot be used., resolve_device() (+29 more)

### Community 2 - "Slide Generation Tool"
Cohesion: 0.14
Nodes (47): add_card(), add_card_text(), add_code_box(), add_footer(), add_forecast_trace(), add_header(), add_pill(), add_shape() (+39 more)

### Community 3 - "Dataset Integrations & Config"
Cohesion: 0.10
Nodes (29): DatasetSearchResult, HuggingFaceDatasetClient, IntegrationError, KaggleDatasetClient, Any, RuntimeError, Stable search and download clients for supported dataset providers., Raised when a provider cannot search or resolve a dataset. (+21 more)

### Community 4 - "TimesFM Concepts & Tutorial"
Cohesion: 0.07
Nodes (34): Dependabot uv Ecosystem Updates, Bug Report Issue Template, Issue Template Config and Contact Links, Pull Request Template, ARIMA, Capability Boundary (Context/Horizon Limits), google/timesfm-2.5-200m-pytorch Checkpoint, Context (C observations) (+26 more)

### Community 5 - "Series Preprocessing & Contracts"
Cohesion: 0.15
Nodes (24): DataQualityReport, PreparedSeries, SeriesSpec, _infer_frequency(), parse_manual_values(), prepare_series(), DataFrame, DatetimeIndex (+16 more)

### Community 6 - "Ingestion Safety & Resolvers"
Cohesion: 0.18
Nodes (22): Client, HostResolver, cache_uploaded_file(), _destination(), download_public_url(), Path, ValueError, Raised when an external source is invalid or unsafe. (+14 more)

### Community 7 - "Provider File Resolution"
Cohesion: 0.20
Nodes (16): ResolvedAsset, _existing_asset(), _is_supported_file(), list_huggingface_files(), ProviderResolutionError, Any, Path, ValueError (+8 more)

### Community 8 - "Desktop Install Docs"
Cohesion: 0.22
Nodes (9): Conda with pip, Python Environment Methods, TimesFM Installation Guide, Repository Cloning on Windows, requirements.txt Dependency Path, TimesFM 2.5 Documentation Screenshot, Streamlit Application, uv Recommended Environment (+1 more)

### Community 9 - "HTML Validation Tooling"
Cohesion: 0.29
Nodes (6): html-validate, dependencies, html-validate, _npx, packages, html-validate@10.9.0

### Community 10 - "Tutorial Docs & README"
Cohesion: 0.33
Nodes (6): TimesFM Foundations, Local Installation, Regular Univariate Series, Forecasting Mastery, Zero to Master Interactive Tutorial, TimesFM Forecast Studio

### Community 11 - "Test Fixtures"
Cohesion: 0.50
Nodes (4): FixtureRequest, Path, _workspace_mkdtemp(), workspace_tmp_path()

## Knowledge Gaps
- **26 isolated node(s):** `html-validate`, `html-validate@10.9.0`, `timesfm-forecasting-app`, `Python Quality Gate`, `Contributor Covenant` (+21 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AppSettings` connect `Dataset Integrations & Config` to `Data Loading & UI Pages`, `Prediction & Forecast Runtime`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._
- **Why does `ResolvedAsset` connect `Provider File Resolution` to `Data Loading & UI Pages`, `Dataset Integrations & Config`, `Series Preprocessing & Contracts`, `Ingestion Safety & Resolvers`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Why does `ForecastRequest` connect `Prediction & Forecast Runtime` to `Data Loading & UI Pages`, `Series Preprocessing & Contracts`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Are the 21 inferred relationships involving `AppSettings` (e.g. with `DatasetSearchResult` and `HuggingFaceDatasetClient`) actually correct?**
  _`AppSettings` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `ForecastRequest` (e.g. with `BatchPrediction` and `DeviceSelectionError`) actually correct?**
  _`ForecastRequest` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `ResolvedAsset` (e.g. with `DatasetSearchResult` and `HuggingFaceDatasetClient`) actually correct?**
  _`ResolvedAsset` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `TimesFMRuntime` (e.g. with `BatchPrediction` and `DeviceSelectionError`) actually correct?**
  _`TimesFMRuntime` has 13 INFERRED edges - model-reasoned connections that need verification._