# LLM.md - Hanzo Insights Python SDK

## Overview
Integrate Hanzo Insights into any Python application. Package name: `hanzo-insights` on PyPI.

## Tech Stack
- **Language**: Python 3.10+
- **Package**: `hanzo_insights` (import name), `hanzo-insights` (pip name)

## Build & Run
```bash
uv sync
uv run pytest
```

## Structure
```
posthog-python/
  hanzo_insights/        # Main package
    __init__.py          # Module-level API, Insights class (alias: Posthog)
    client.py            # Client class
    ai/                  # AI provider integrations (OpenAI, Anthropic, Gemini, LangChain)
    integrations/        # Framework integrations (Django middleware)
    test/                # Tests
  examples/
  integration_tests/
  pyproject.toml         # Package config (name: hanzo-insights)
  setup.py               # Legacy setup
```

## Key Files
- `pyproject.toml` -- Package config, dependencies, test config
- `hanzo_insights/__init__.py` -- Public API surface
- `hanzo_insights/client.py` -- Client implementation

## Rebrand Notes
- Main class: `Insights` (backward compat alias: `Posthog = Insights`)
- Django middleware: `InsightsContextMiddleware` (alias: `PosthogContextMiddleware`)
- OpenAI Agents: `InsightsTracingProcessor` (alias: `PostHogTracingProcessor`)
- Internal protocol values (`$lib`, `posthog.com` ingestion URLs) kept for server compat
- `posthog_*` parameter names in AI wrappers kept for API compat
