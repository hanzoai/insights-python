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
    __init__.py          # Module-level API, Insights class
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
- Main class: `Insights` (no backward compat aliases)
- Django middleware: `InsightsContextMiddleware` (no backward compat aliases)
- OpenAI Agents: `InsightsTracingProcessor` (no backward compat aliases)
- `$lib` protocol value: `insights-python`
- Ingestion URLs: `us.i.insights.hanzo.ai` / `eu.i.insights.hanzo.ai`
- AI wrapper kwargs: `insights_*` (e.g. `insights_distinct_id`, `insights_trace_id`)
- Exception attrs: `__insights_exception_captured`, `__insights_exception_uuid`
- Context var: `insights_context_stack`
- Redis prefix: `insights:flags:`
- Redaction sentinels: `$$_insights_redacted_*`, `$$_insights_value_too_long_*`
- Django settings: `INSIGHTS_MW_*` only (no `POSTHOG_MW_*` fallback)
- Django headers: `X-INSIGHTS-SESSION-ID`, `X-INSIGHTS-DISTINCT-ID` only
