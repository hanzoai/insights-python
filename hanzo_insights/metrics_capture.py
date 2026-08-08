"""Measurements — counters, gauges and histograms — recorded as events.

A measurement is an event named `$metric` carrying the metric's name, kind,
value and unit, with the caller's attributes as ordinary event properties so
they break down in the product like any other dimension.

Recording a sample and aggregating samples are separate jobs. This records:
one event per measurement, on the client's existing queue and consumer, so a
metric travels the same path as every other event and needs no second
transport. Aggregation is a query: sum the counters, take quantiles of the
histograms, read the last value of a gauge.
"""

import logging
from typing import TYPE_CHECKING, Mapping, Optional, Union

if TYPE_CHECKING:
    from hanzo_insights.client import Client

METRIC_EVENT = "$metric"

COUNT = "count"
GAUGE = "gauge"
HISTOGRAM = "histogram"

MetricValue = Union[int, float]
MetricAttributes = Mapping[str, Union[str, int, float, bool]]


class InsightsMetrics:
    """Records measurements through a client.

    Examples:
        ```python
        client.metrics.count("warehouse.backfill.started", 1, attributes={"dataset": "events"})
        client.metrics.histogram("warehouse.backfill.duration", 2.5, unit="s", attributes={"dataset": "events"})
        client.metrics.gauge("warehouse.backfill.last.success.timestamp", time.time(), unit="s")
        ```
    """

    log = logging.getLogger("hanzo_insights")

    def __init__(self, client: "Client"):
        self.client = client

    def count(
        self,
        name: str,
        value: MetricValue,
        *,
        unit: Optional[str] = None,
        attributes: Optional[MetricAttributes] = None,
    ) -> None:
        """Add `value` to the counter `name`. The sample is the delta, not the running total."""
        self._record(COUNT, name, value, unit, attributes)

    def gauge(
        self,
        name: str,
        value: MetricValue,
        *,
        unit: Optional[str] = None,
        attributes: Optional[MetricAttributes] = None,
    ) -> None:
        """Set the gauge `name` to `value`. The latest sample is the current reading."""
        self._record(GAUGE, name, value, unit, attributes)

    def histogram(
        self,
        name: str,
        value: MetricValue,
        *,
        unit: Optional[str] = None,
        attributes: Optional[MetricAttributes] = None,
    ) -> None:
        """Record one observation of `name`, to be summarized over a period."""
        self._record(HISTOGRAM, name, value, unit, attributes)

    def flush(self) -> None:
        """Block until every queued measurement has been attempted."""
        self.client.flush()

    def _record(
        self,
        kind: str,
        name: str,
        value: MetricValue,
        unit: Optional[str],
        attributes: Optional[MetricAttributes],
    ) -> None:
        # Attributes go in first so the reserved keys always win: an attribute
        # named `$metric_name` must not be able to rename the metric.
        properties = {
            **dict(attributes or {}),
            "$metric_name": name,
            "$metric_kind": kind,
            "$metric_value": value,
            "$metric_unit": unit,
        }
        # No distinct_id: a measurement belongs to the system, not to a person,
        # so it is captured personless and creates no person profile.
        self.client.capture(METRIC_EVENT, properties=properties)
