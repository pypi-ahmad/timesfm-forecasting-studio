# Graph Report - .  (2026-07-31)

## Corpus Check
- Corpus is ~38,698 words - fits in a single context window. You may not need a graph.

## Summary
- 505 nodes · 1210 edges · 29 communities (24 shown, 5 thin omitted)
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 261 edges (avg confidence: 0.72)
- Token cost: 152,707 input · 17,000 output

## Community Hubs (Navigation)
- Prediction & Forecast Runtime
- Dataset Integrations & Config
- Slide Deck Generation
- Manual Dataset Curation
- Series Preprocessing & Contracts
- Data Loading & Caching
- Ingestion Safety & Resolvers
- Analysis & Report Generation
- Provider File Resolution
- Backtest Evaluation
- Core Docs & Bridge Concepts
- Environment & Credential Setup
- Data Engineering Concepts
- Forecasting Mastery & Visualization
- Manual Dataset Sources
- Desktop Installation Guide
- Model Comparison & Boundaries
- Compilation & Context Config
- UI State Management
- Repo Governance & CI
- Installation Method Setup
- Test Fixtures
- Forecasting Package Init
- Ingestion Package Init
- App Package Init
- UI Package Init
- Package Root

## God Nodes (most connected - your core abstractions)
1. `AppSettings` - 45 edges
2. `ForecastRequest` - 29 edges
3. `ResolvedAsset` - 28 edges
4. `TimesFMRuntime` - 27 edges
5. `create_studio_slide()` - 19 edges
6. `ForecastResult` - 18 edges
7. `prepare_series()` - 18 edges
8. `add_text()` - 17 edges
9. `download_public_url()` - 17 edges
10. `create_pitfalls_slide()` - 16 edges

## Surprising Connections (you probably didn't know these)
- `CI Workflow (Python 3.14 Quality Gate)` --semantically_similar_to--> `requirements.txt (pip-compatible pinned dependencies)`  [INFERRED] [semantically similar]
  .github/workflows/ci.yml → requirements.txt
- `TimesFM Zero to Master (index.html interactive tutorial site)` --semantically_similar_to--> `End-to-End Prediction Path`  [INFERRED] [semantically similar]
  index.html → docs/tutorial/04_forecasting_mastery.md
- `Documentation Issue Form` --references--> `Data Ingestion Architecture (Local/URL/Kaggle/HF to DataFrame)`  [AMBIGUOUS]
  .github/ISSUE_TEMPLATE/documentation.yml → docs/tutorial/03_data_engineering.md
- `CI Workflow (Python 3.14 Quality Gate)` --shares_data_with--> `Installation Troubleshooting Matrix`  [INFERRED]
  .github/workflows/ci.yml → docs/tutorial/02_local_installation.md
- `TimesFM Zero to Master (index.html interactive tutorial site)` --semantically_similar_to--> `Time Series and Forecasting Fundamentals`  [INFERRED] [semantically similar]
  index.html → docs/tutorial/01_timesfm_intro.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Community/Governance Documentation Set** — contributing_contributingguide, code_of_conduct_contributorcovenant, security_securitypolicy, support_supportguide, github_pull_request_template_pullrequesttemplate [INFERRED 0.85]
- **Zero-to-Master Tutorial (4 Chapters)** — docs_tutorial_01_timesfm_intro_timeseriesforecasting, docs_tutorial_02_local_installation_runtimecontract, docs_tutorial_03_data_engineering_ingestionarchitecture, docs_tutorial_04_forecasting_mastery_predictionpath, index_html_timesfmzerotomasterdocs [EXTRACTED 1.00]
- **Multi-Source Dataset Ingestion (Local/URL/Kaggle/HF)** — docs_tutorial_03_data_engineering_localfileloading, docs_tutorial_03_data_engineering_publicurlloading, docs_tutorial_03_data_engineering_kaggleretrieval, docs_tutorial_03_data_engineering_hfretrieval [EXTRACTED 1.00]

## Communities (29 total, 5 thin omitted)

### Community 0 - "Prediction & Forecast Runtime"
Cohesion: 0.07
Nodes (45): BatchPrediction, DeviceSelectionError, PredictionOutput, DeviceChoice, ValueError, Pandas-oriented TimesFM predictor facade., Raised when a requested compute device cannot be used., resolve_device() (+37 more)

### Community 1 - "Dataset Integrations & Config"
Cohesion: 0.08
Nodes (36): DatasetSearchResult, HuggingFaceDatasetClient, IntegrationError, KaggleDatasetClient, Any, RuntimeError, Stable search and download clients for supported dataset providers., Raised when a provider cannot search or resolve a dataset. (+28 more)

### Community 2 - "Slide Deck Generation"
Cohesion: 0.14
Nodes (47): add_card(), add_card_text(), add_code_box(), add_footer(), add_forecast_trace(), add_header(), add_pill(), add_shape() (+39 more)

### Community 3 - "Manual Dataset Curation"
Cohesion: 0.11
Nodes (38): Download five ready-to-upload datasets for local manual app testing., build_appliance_series(), build_bikeshare_series(), build_dataset_suite(), build_fred_series(), build_noaa_series(), build_taxi_series(), DatasetValidationError (+30 more)

### Community 4 - "Series Preprocessing & Contracts"
Cohesion: 0.12
Nodes (28): DataQualityReport, PreparedSeries, SeriesSpec, _infer_frequency(), parse_manual_values(), prepare_series(), DataFrame, DatetimeIndex (+20 more)

### Community 5 - "Data Loading & Caching"
Cohesion: 0.13
Nodes (31): cache_uploads(), detect_datetime_columns(), load_dataset(), load_remote_dataset(), LoadedDataset, DataFrame, Path, Stable data-loading facade for local files and public URLs. (+23 more)

### Community 6 - "Ingestion Safety & Resolvers"
Cohesion: 0.14
Nodes (26): Client, HostResolver, list_excel_sheets(), DataFrame, Path, read_tabular(), cache_uploaded_file(), _destination() (+18 more)

### Community 7 - "Analysis & Report Generation"
Cohesion: 0.14
Nodes (22): analyze_series(), EdaResult, DatetimeIndex, ndarray, _build_html(), _build_pdf(), build_report_bundle(), _csv_bytes() (+14 more)

### Community 8 - "Provider File Resolution"
Cohesion: 0.20
Nodes (15): _existing_asset(), _is_supported_file(), list_huggingface_files(), ProviderResolutionError, Any, Path, ValueError, Raised when a dataset provider cannot yield a supported file. (+7 more)

### Community 9 - "Backtest Evaluation"
Cohesion: 0.24
Nodes (14): anomaly_frame(), BacktestResult, build_rolling_origins(), calculate_metrics(), DataFrame, DatetimeIndex, ndarray, run_rolling_backtest() (+6 more)

### Community 10 - "Core Docs & Bridge Concepts"
Cohesion: 0.27
Nodes (14): Time Series and Forecasting Fundamentals, Time-Series Foundation Model (TSFM), Installation Runtime Contract (Python/uv/PyTorch/TimesFM versions), Data Ingestion Architecture (Local/URL/Kaggle/HF to DataFrame), Google Research TimesFM Repository, Bug Report Issue Form, Issue Template Chooser Config, Documentation Issue Form (+6 more)

### Community 11 - "Environment & Credential Setup"
Cohesion: 0.17
Nodes (13): CPU versus CUDA Device Selection, Hugging Face Authentication and Caching, Kaggle Credentials Configuration, Offline Mode (TIMESFM_OFFLINE), Installation Troubleshooting Matrix, Data-Quality Workflow (Semantics/Timestamp/Uniqueness/Regularity/Missingness/Context/Leakage Gates), Retrieving Hugging Face Datasets (HfApi/hf_hub_download), Retrieving Kaggle Datasets (owner/dataset handles) (+5 more)

### Community 12 - "Data Engineering Concepts"
Cohesion: 0.17
Nodes (12): Datetime Detection and Parsing, Frequency Inference (pandas.infer_freq), Linear Interpolation Mathematics for Internal Gaps, Loading Local Files (Content-Addressed Cache), Target Conversion and Missing Value Handling, Loading a Public URL (Untrusted Remote Resolver), Supported File Formats (CSV/Parquet/XLSX), Required Timestamp Invariants (Parse/Sort/Unique/Regular) (+4 more)

### Community 13 - "Forecasting Mastery & Visualization"
Cohesion: 0.20
Nodes (10): Probabilistic Quantile Outputs (Pinball Loss), Evaluation Before Production (Rolling-Origin Backtesting), Forecasting Failure Matrix, Manual Simulator (Numeric Sequence Parser), Performance and OOM Control Levers, Practical Parameter Recipes (Hourly/Daily/Monthly), Quantile Interpretation and Empirical Coverage, Understanding Point/Distribution Outputs (B,H) and (B,H,10) (+2 more)

### Community 14 - "Manual Dataset Sources"
Cohesion: 0.22
Nodes (9): Changelog Entry 0.2.0, download_manual_datasets.py Script, FRED UNRATE Dataset (US Unemployment Monthly), Manual Dataset Suite, NOAA GHCN-D Dataset (Central Park Daily Temperature), NYC TLC Yellow Taxi Trip Records Dataset, UCI Appliances Energy Prediction Dataset, UCI Bike Sharing Dataset (Capital Bikeshare Hourly) (+1 more)

### Community 15 - "Desktop Installation Guide"
Cohesion: 0.22
Nodes (9): Conda with pip, Python Environment Methods, TimesFM Installation Guide, Repository Cloning on Windows, requirements.txt Dependency Path, TimesFM 2.5 Documentation Screenshot, Streamlit Application, uv Recommended Environment (+1 more)

### Community 16 - "Model Comparison & Boundaries"
Cohesion: 0.29
Nodes (7): Capability Boundary of the Repository, TimesFM 2.5 Frequency Indicator Removal, TimesFM vs ARIMA/Prophet/DeepAR Comparison, Zero-Shot Transfer Learning, Prophet Documentation, statsmodels ARIMA API Reference, Salinas et al. - DeepAR: Probabilistic Forecasting with Autoregressive Recurrent Networks

### Community 17 - "Compilation & Context Config"
Cohesion: 0.29
Nodes (7): Patching (Input/Output Patch Mechanism), Dimension Matching and Compilation Buckets (32/128-point rounding), Context Length Selection, Forecast Horizon Selection, Frequency and Seasonality Contract, End-to-End Prediction Path, Runtime ForecastConfig Options

### Community 18 - "UI State Management"
Cohesion: 0.33
Nodes (5): clear_dataset_state(), Any, Clear session data while leaving the content-addressed disk cache intact., test_clear_dataset_state_initializes_missing_uploader_generation(), test_clear_dataset_state_removes_loaded_data_results_and_rotates_uploader()

### Community 19 - "Repo Governance & CI"
Cohesion: 0.50
Nodes (5): Contributor Covenant Code of Conduct, Contributing Guide, Dependabot Configuration, Pull Request Template, CI Workflow (Python 3.14 Quality Gate)

### Community 20 - "Installation Method Setup"
Cohesion: 0.60
Nodes (5): Conda Environment Alternative Setup, uv Setup (Recommended Environment Method), venv + pip Alternative Setup, Astral uv Installation Docs, requirements.txt (pip-compatible pinned dependencies)

### Community 21 - "Test Fixtures"
Cohesion: 0.50
Nodes (4): FixtureRequest, Path, _workspace_mkdtemp(), workspace_tmp_path()

## Ambiguous Edges - Review These
- `Documentation Issue Form` → `Data Ingestion Architecture (Local/URL/Kaggle/HF to DataFrame)`  [AMBIGUOUS]
  .github/ISSUE_TEMPLATE/documentation.yml · relation: references

## Knowledge Gaps
- **26 isolated node(s):** `timesfm-forecasting-app`, `TimesFM 2.5 Documentation Screenshot`, `Repository Cloning on Windows`, `Conda with pip`, `requirements.txt Dependency Path` (+21 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Documentation Issue Form` and `Data Ingestion Architecture (Local/URL/Kaggle/HF to DataFrame)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `AppSettings` connect `Dataset Integrations & Config` to `Prediction & Forecast Runtime`, `Data Loading & Caching`, `Analysis & Report Generation`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Why does `ResolvedAsset` connect `Data Loading & Caching` to `Provider File Resolution`, `Dataset Integrations & Config`, `Series Preprocessing & Contracts`, `Ingestion Safety & Resolvers`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Why does `ForecastRequest` connect `Prediction & Forecast Runtime` to `Series Preprocessing & Contracts`, `Data Loading & Caching`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `AppSettings` (e.g. with `DatasetSearchResult` and `HuggingFaceDatasetClient`) actually correct?**
  _`AppSettings` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `ForecastRequest` (e.g. with `BatchPrediction` and `DeviceSelectionError`) actually correct?**
  _`ForecastRequest` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `ResolvedAsset` (e.g. with `DatasetSearchResult` and `HuggingFaceDatasetClient`) actually correct?**
  _`ResolvedAsset` has 11 INFERRED edges - model-reasoned connections that need verification._