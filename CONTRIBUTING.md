# Contributing to TimesFM Forecast Studio

Thank you for improving the project. Contributions should remain focused, reproducible, and consistent with the local-first architecture.

## Before opening work

| Change | First step |
|---|---|
| Bug | Search existing issues and include a minimal reproducer |
| Feature | Open a feature request describing the user problem and tradeoff |
| Documentation | Identify the inaccurate or missing reader outcome |
| Security issue | Stop and follow [SECURITY.md](SECURITY.md); do not open a public issue |

Do not submit model weights, datasets containing restricted data, credentials, caches, or generated virtual environments.

## Development setup

```powershell
git clone https://github.com/OWNER/REPOSITORY.git
Set-Location REPOSITORY
uv python install 3.14
uv sync --locked --group dev
```

`pyproject.toml` and `uv.lock` are canonical. Add or update Python dependencies with uv and commit the resulting lockfile. Keep `requirements.txt` synchronized when direct runtime dependencies change.

## Change principles

| Principle | Expected behavior |
|---|---|
| Small scope | Solve the reported problem without unrelated refactors |
| Existing architecture | Use current contracts, facades, error types, and test patterns |
| Public boundaries | Validate external files, URLs, credentials, and model output shapes |
| Secrets | Use environment variables or Streamlit secrets; never log token values |
| Documentation | Explain changed user behavior and non-obvious tradeoffs |
| Dependencies | Prefer existing packages and justify material additions |

## Testing

Run the complete local gate before opening a pull request:

```powershell
uv sync --locked --group dev
uv run ruff check src tests app.py
uv run ruff format --check src tests app.py
uv run pytest
```

Behavior changes require tests of the public contract. Bug fixes should add a failing reproducer before the fix. Model-facing tests must use test doubles by default so CI does not download checkpoint weights or require a GPU.

## Documentation style

- Prefer tables and small diagrams when they clarify repeated relationships.
- Use exact repository values and cite current primary documentation for external APIs.
- Mark important operational risks with a concise `> ⚠️` callout.
- Check relative links and keep the four tutorial chapters navigable in order.
- Do not claim forecast accuracy without a documented evaluation dataset and protocol.

## Pull requests

A pull request should contain one coherent change and explain:

1. What problem it solves.
2. Why the chosen approach fits the current architecture.
3. How reviewers can verify it.
4. What remains risky or intentionally out of scope.

Complete the pull-request template, link the relevant issue, and keep generated caches or debug artifacts out of the diff. Maintainers may request a smaller change if review or rollback would otherwise be difficult.

## Commit messages

Use imperative, focused messages such as:

```text
fix: reject malformed forecast distribution shapes
docs: explain frequency handling in TimesFM 2.5
test: cover month-end future index generation
```

## Conduct and licensing

Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). By contributing, you agree that your contribution is licensed under the repository's [MIT License](LICENSE).
