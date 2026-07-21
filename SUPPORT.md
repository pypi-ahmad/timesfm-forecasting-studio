# Support

## Find the right channel

| Need | Channel |
|---|---|
| Installation or usage question | Read the tutorial and search existing issues first |
| Reproducible application defect | Bug report issue form |
| Focused product improvement | Feature request issue form |
| Incorrect or unclear documentation | Documentation issue form |
| Vulnerability or sensitive report | Follow [SECURITY.md](SECURITY.md), never a public issue |
| TimesFM model behavior/API | Consult the [official TimesFM repository](https://github.com/google-research/timesfm) |

## Before requesting help

Include the smallest safe evidence that reproduces the problem:

- Operating system and Python version.
- Output of `uv --version` and the relevant package version.
- Auto/CPU/CUDA selection and non-secret Torch device information.
- Exact command and full error message.
- A synthetic or public minimal dataset.
- Context, horizon, and frequency values.

Do not post access tokens, `kaggle.json`, `.streamlit/secrets.toml`, private dataset rows, signed URL queries, or full environment dumps.

## Project boundaries

This is a community repository without guaranteed response times, hosted service support, forecasting advice, or accuracy guarantees. Questions about account billing, provider outages, gated assets, and upstream license terms belong with the relevant provider.

For installation and forecasting guidance, start with the [Zero-to-Master tutorial](docs/tutorial/01_timesfm_intro.md).
