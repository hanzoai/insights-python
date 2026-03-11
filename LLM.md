# LLM.md - Hanzo Posthog Python

## Overview
Integrate Hanzo Insights into any python application.

## Tech Stack
- **Language**: Python

## Build & Run
```bash
uv sync
uv run pytest
```

## Structure
```
posthog-python/
  BEFORE_SEND.md
  CHANGELOG.md
  CODEOWNERS
  LICENSE
  MANIFEST.in
  Makefile
  README.md
  README_ANALYTICS.md
  bin/
  e2e_test.sh
  example.py
  examples/
  hanzo_insights/
  integration_tests/
  mypy-baseline.txt
```

## Key Files
- `README.md` -- Project documentation
- `pyproject.toml` -- Python project config
- `Makefile` -- Build automation
