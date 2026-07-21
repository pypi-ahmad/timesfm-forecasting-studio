# Security Policy

## Supported versions

Security fixes are applied to the latest code on the default branch. The project is currently pre-1.0 and does not promise fixes for older snapshots.

| Version | Supported |
|---|---:|
| Latest default branch | Yes |
| Older commits or forks | No |

## Reporting a vulnerability

Do not disclose suspected vulnerabilities in public issues, discussions, pull requests, screenshots, logs, or example datasets.

Use GitHub's **Report a vulnerability** control on the repository Security page. If private vulnerability reporting is not enabled, contact the maintainer through the private method published on the [maintainer's GitHub profile](https://github.com/pypi-ahmad) and request a secure reporting channel without including exploit details in the initial public message.

Include only what is necessary for reproduction:

| Information | Example |
|---|---|
| Affected component/version | URL resolver on current default branch |
| Impact | Local network access, credential exposure, arbitrary file write |
| Preconditions | Attacker controls a dataset URL |
| Reproduction | Minimal safe request and observed result |
| Suggested mitigation | Optional and clearly separated from evidence |

Never include real credentials, personal data, proprietary datasets, or destructive payloads. Use synthetic values and redact tokens from logs.

## Response expectations

The maintainer will acknowledge a complete report when practical, validate severity and affected versions, coordinate a fix, and credit the reporter if requested and safe. Timelines depend on impact and maintainer availability; no service-level agreement is promised.

Please allow a reasonable remediation window before public disclosure. If a report is not a security issue, it may be redirected to the normal issue tracker after sensitive details are removed.

## Security boundaries

The application processes untrusted local and remote tabular files in the local Python process. It applies URL scheme, DNS/IP, redirect, size, extension, and signature checks, but compressed XLSX/Parquet content can still consume substantial memory. Provider tokens and model/data caches remain the operator's responsibility.

TimesFM weights, Kaggle, Hugging Face, PyTorch, Streamlit, and other dependencies have separate security and disclosure processes. Report upstream vulnerabilities to the affected upstream project as well as this project when the integration creates project-specific impact.
