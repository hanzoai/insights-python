try:
    import anthropic
except ImportError:
    raise ModuleNotFoundError(
        "Please install the Anthropic SDK to use this feature: 'pip install anthropic'"
    )

from typing import Optional

from hanzo_insights.ai.anthropic.anthropic import WrappedMessages
from hanzo_insights.ai.anthropic.anthropic_async import AsyncWrappedMessages
from hanzo_insights.client import Client as InsightsClient
from hanzo_insights import setup


class AnthropicBedrock(anthropic.AnthropicBedrock):
    """
    A wrapper around the Anthropic Bedrock SDK that automatically sends LLM usage events to Insights.
    """

    _ph_client: InsightsClient

    def __init__(self, posthog_client: Optional[InsightsClient] = None, **kwargs):
        super().__init__(**kwargs)
        self._ph_client = posthog_client or setup()
        self.messages = WrappedMessages(self)


class AsyncAnthropicBedrock(anthropic.AsyncAnthropicBedrock):
    """
    A wrapper around the Anthropic Bedrock SDK that automatically sends LLM usage events to Insights.
    """

    _ph_client: InsightsClient

    def __init__(self, posthog_client: Optional[InsightsClient] = None, **kwargs):
        super().__init__(**kwargs)
        self._ph_client = posthog_client or setup()
        self.messages = AsyncWrappedMessages(self)


class AnthropicVertex(anthropic.AnthropicVertex):
    """
    A wrapper around the Anthropic Vertex SDK that automatically sends LLM usage events to Insights.
    """

    _ph_client: InsightsClient

    def __init__(self, posthog_client: Optional[InsightsClient] = None, **kwargs):
        super().__init__(**kwargs)
        self._ph_client = posthog_client or setup()
        self.messages = WrappedMessages(self)


class AsyncAnthropicVertex(anthropic.AsyncAnthropicVertex):
    """
    A wrapper around the Anthropic Vertex SDK that automatically sends LLM usage events to Insights.
    """

    _ph_client: InsightsClient

    def __init__(self, posthog_client: Optional[InsightsClient] = None, **kwargs):
        super().__init__(**kwargs)
        self._ph_client = posthog_client or setup()
        self.messages = AsyncWrappedMessages(self)
