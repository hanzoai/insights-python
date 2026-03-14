try:
    import anthropic
    from anthropic.resources import Messages
except ImportError:
    raise ModuleNotFoundError(
        "Please install the Anthropic SDK to use this feature: 'pip install anthropic'"
    )

import time
import uuid
from typing import Any, Dict, List, Optional

from hanzo_insights.ai.types import StreamingContentBlock, TokenUsage, ToolInProgress
from hanzo_insights.ai.utils import (
    call_llm_and_track_usage,
    merge_usage_stats,
)
from hanzo_insights.ai.anthropic.anthropic_converter import (
    extract_anthropic_usage_from_event,
    handle_anthropic_content_block_start,
    handle_anthropic_text_delta,
    handle_anthropic_tool_delta,
    finalize_anthropic_tool_input,
)
from hanzo_insights.ai.sanitization import sanitize_anthropic
from hanzo_insights.client import Client as InsightsClient
from hanzo_insights import setup


class Anthropic(anthropic.Anthropic):
    """
    A wrapper around the Anthropic SDK that automatically sends LLM usage events to Insights.
    """

    _ph_client: InsightsClient

    def __init__(self, insights_client: Optional[InsightsClient] = None, **kwargs):
        """
        Args:
            insights_client: Insights client for tracking usage
            **kwargs: Additional arguments passed to the Anthropic client
        """
        super().__init__(**kwargs)
        self._ph_client = insights_client or setup()
        self.messages = WrappedMessages(self)


class WrappedMessages(Messages):
    _client: Anthropic

    def create(
        self,
        insights_distinct_id: Optional[str] = None,
        insights_trace_id: Optional[str] = None,
        insights_properties: Optional[Dict[str, Any]] = None,
        insights_privacy_mode: bool = False,
        insights_groups: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        """
        Create a message using Anthropic's API while tracking usage in Insights.

        Args:
            insights_distinct_id: Optional ID to associate with the usage event
            insights_trace_id: Optional trace UUID for linking events
            insights_properties: Optional dictionary of extra properties to include in the event
            insights_privacy_mode: Whether to redact sensitive information in tracking
            insights_groups: Optional group analytics properties
            **kwargs: Arguments passed to Anthropic's messages.create
        """

        if insights_trace_id is None:
            insights_trace_id = str(uuid.uuid4())

        if kwargs.get("stream", False):
            return self._create_streaming(
                insights_distinct_id,
                insights_trace_id,
                insights_properties,
                insights_privacy_mode,
                insights_groups,
                **kwargs,
            )

        return call_llm_and_track_usage(
            insights_distinct_id,
            self._client._ph_client,
            "anthropic",
            insights_trace_id,
            insights_properties,
            insights_privacy_mode,
            insights_groups,
            self._client.base_url,
            super().create,
            **kwargs,
        )

    def stream(
        self,
        insights_distinct_id: Optional[str] = None,
        insights_trace_id: Optional[str] = None,
        insights_properties: Optional[Dict[str, Any]] = None,
        insights_privacy_mode: bool = False,
        insights_groups: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        if insights_trace_id is None:
            insights_trace_id = str(uuid.uuid4())

        return self._create_streaming(
            insights_distinct_id,
            insights_trace_id,
            insights_properties,
            insights_privacy_mode,
            insights_groups,
            **kwargs,
        )

    def _create_streaming(
        self,
        insights_distinct_id: Optional[str],
        insights_trace_id: Optional[str],
        insights_properties: Optional[Dict[str, Any]],
        insights_privacy_mode: bool,
        insights_groups: Optional[Dict[str, Any]],
        **kwargs: Any,
    ):
        start_time = time.time()
        usage_stats: TokenUsage = TokenUsage(input_tokens=0, output_tokens=0)
        accumulated_content = ""
        content_blocks: List[StreamingContentBlock] = []
        tools_in_progress: Dict[str, ToolInProgress] = {}
        current_text_block: Optional[StreamingContentBlock] = None
        response = super().create(**kwargs)

        def generator():
            nonlocal usage_stats
            nonlocal accumulated_content
            nonlocal content_blocks
            nonlocal tools_in_progress
            nonlocal current_text_block

            try:
                for event in response:
                    # Extract usage stats from event
                    event_usage = extract_anthropic_usage_from_event(event)
                    merge_usage_stats(usage_stats, event_usage)

                    # Handle content block start events
                    if hasattr(event, "type") and event.type == "content_block_start":
                        block, tool = handle_anthropic_content_block_start(event)

                        if block:
                            content_blocks.append(block)

                            if block.get("type") == "text":
                                current_text_block = block
                            else:
                                current_text_block = None

                        if tool:
                            tool_id = tool["block"].get("id")
                            if tool_id:
                                tools_in_progress[tool_id] = tool

                    # Handle text delta events
                    delta_text = handle_anthropic_text_delta(event, current_text_block)

                    if delta_text:
                        accumulated_content += delta_text

                    # Handle tool input delta events
                    handle_anthropic_tool_delta(
                        event, content_blocks, tools_in_progress
                    )

                    # Handle content block stop events
                    if hasattr(event, "type") and event.type == "content_block_stop":
                        current_text_block = None
                        finalize_anthropic_tool_input(
                            event, content_blocks, tools_in_progress
                        )

                    yield event

            finally:
                end_time = time.time()
                latency = end_time - start_time

                self._capture_streaming_event(
                    insights_distinct_id,
                    insights_trace_id,
                    insights_properties,
                    insights_privacy_mode,
                    insights_groups,
                    kwargs,
                    usage_stats,
                    latency,
                    content_blocks,
                    accumulated_content,
                )

        return generator()

    def _capture_streaming_event(
        self,
        insights_distinct_id: Optional[str],
        insights_trace_id: Optional[str],
        insights_properties: Optional[Dict[str, Any]],
        insights_privacy_mode: bool,
        insights_groups: Optional[Dict[str, Any]],
        kwargs: Dict[str, Any],
        usage_stats: TokenUsage,
        latency: float,
        content_blocks: List[StreamingContentBlock],
        accumulated_content: str,
    ):
        from hanzo_insights.ai.types import StreamingEventData
        from hanzo_insights.ai.anthropic.anthropic_converter import (
            format_anthropic_streaming_input,
            format_anthropic_streaming_output_complete,
        )
        from hanzo_insights.ai.utils import capture_streaming_event

        # Prepare standardized event data
        formatted_input = format_anthropic_streaming_input(kwargs)
        sanitized_input = sanitize_anthropic(formatted_input)

        event_data = StreamingEventData(
            provider="anthropic",
            model=kwargs.get("model", "unknown"),
            base_url=str(self._client.base_url),
            kwargs=kwargs,
            formatted_input=sanitized_input,
            formatted_output=format_anthropic_streaming_output_complete(
                content_blocks, accumulated_content
            ),
            usage_stats=usage_stats,
            latency=latency,
            distinct_id=insights_distinct_id,
            trace_id=insights_trace_id,
            properties=insights_properties,
            privacy_mode=insights_privacy_mode,
            groups=insights_groups,
        )

        # Use the common capture function
        capture_streaming_event(self._client._ph_client, event_data)
