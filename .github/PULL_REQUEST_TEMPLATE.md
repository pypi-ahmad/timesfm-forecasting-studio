## What changed

Describe the user-visible or engineering outcome. Keep the pull request focused on one coherent change.

## Why

Explain the problem, relevant constraints, and why this approach fits the existing architecture.

## Verification

List exact commands and manual scenarios used to verify the change.

```text
uv run ruff check src tests app.py
uv run ruff format --check src tests app.py
uv run pytest
```

## Risk and rollback

Describe residual risk, compatibility impact, cache/model implications, and how the change can be reverted safely.

## Checklist

- [ ] I linked the relevant issue or explained why none exists.
- [ ] I added or updated public-contract tests for behavior changes.
- [ ] I updated user-facing documentation where needed.
- [ ] I introduced no credentials, private datasets, model weights, or cache artifacts.
- [ ] I reviewed the complete diff for unrelated changes.
- [ ] I ran the verification commands above and recorded any exceptions.
