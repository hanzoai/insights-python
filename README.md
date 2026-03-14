# Hanzo Insights Python SDK

Integrate [Hanzo Insights](https://insights.hanzo.ai) into any Python application.

## Installation

```bash
pip install hanzo-insights
```

## Quick Start

```python
from hanzo_insights import Insights

client = Insights('<your_project_api_key>', host='https://insights.hanzo.ai')

# Capture an event
client.capture('user_123', 'purchase', properties={'product': 'widget'})

# Feature flags
if client.feature_enabled('new-checkout', 'user_123'):
    show_new_checkout()
```

## Module-level usage

```python
import hanzo_insights

hanzo_insights.api_key = '<your_project_api_key>'
hanzo_insights.host = 'https://insights.hanzo.ai'

hanzo_insights.capture('movie_played', distinct_id='user_123', properties={'movie_id': '42'})
hanzo_insights.shutdown()
```

## Python Version Support

| SDK Version    | Python Versions Supported     |
| -------------- | ----------------------------- |
| 7.3.1+         | 3.10, 3.11, 3.12, 3.13, 3.14 |
| 7.0.0 - 7.0.1  | 3.10, 3.11, 3.12, 3.13       |
| 4.0.1 - 6.x    | 3.9, 3.10, 3.11, 3.12, 3.13  |

## Development

We use [uv](https://docs.astral.sh/uv/).

```bash
uv python install 3.12
uv python pin 3.12
uv venv
source env/bin/activate
uv sync --extra dev --extra test
pre-commit install
make test
```

### Running Tests

```bash
make test
# or run a specific test:
pytest -k test_no_api_key
```

## Backward Compatibility

For users migrating from `posthog` or `posthoganalytics`, the `Posthog` class name is
available as an alias for `Insights`:

```python
from hanzo_insights import Posthog  # works, same as Insights
```

## License

MIT
