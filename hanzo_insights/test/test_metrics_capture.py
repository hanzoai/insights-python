import unittest

import mock

from hanzo_insights.client import Client
from hanzo_insights.metrics_capture import METRIC_EVENT, InsightsMetrics
from hanzo_insights.test.test_utils import FAKE_TEST_API_KEY


class TestMetricsCapture(unittest.TestCase):
    def setUp(self):
        self.client = Client(FAKE_TEST_API_KEY, sync_mode=True)

    def captured(self, record):
        """Run `record` against a client whose delivery is mocked, return the one message."""
        with mock.patch("hanzo_insights.client.batch_post") as mock_post:
            record(self.client.metrics)
            mock_post.assert_called_once()
            batch = mock_post.call_args[1]["batch"]
            self.assertEqual(len(batch), 1)
            return batch[0]

    def test_client_has_metrics(self):
        self.assertIsInstance(self.client.metrics, InsightsMetrics)

    def test_count(self):
        msg = self.captured(
            lambda m: m.count(
                "warehouse.backfill.started", 1, attributes={"dataset": "events"}
            )
        )
        self.assertEqual(msg["event"], METRIC_EVENT)
        properties = msg["properties"]
        self.assertEqual(properties["$metric_name"], "warehouse.backfill.started")
        self.assertEqual(properties["$metric_kind"], "count")
        self.assertEqual(properties["$metric_value"], 1)
        self.assertIsNone(properties["$metric_unit"])
        self.assertEqual(properties["dataset"], "events")

    def test_histogram_carries_its_unit(self):
        msg = self.captured(
            lambda m: m.histogram(
                "warehouse.backfill.duration",
                2.5,
                unit="s",
                attributes={"mode": "daily"},
            )
        )
        properties = msg["properties"]
        self.assertEqual(properties["$metric_kind"], "histogram")
        self.assertEqual(properties["$metric_value"], 2.5)
        self.assertEqual(properties["$metric_unit"], "s")
        self.assertEqual(properties["mode"], "daily")

    def test_gauge(self):
        msg = self.captured(
            lambda m: m.gauge(
                "warehouse.backfill.last.success.timestamp", 123.0, unit="s"
            )
        )
        properties = msg["properties"]
        self.assertEqual(properties["$metric_kind"], "gauge")
        self.assertEqual(properties["$metric_value"], 123.0)

    def test_measurement_is_personless(self):
        msg = self.captured(lambda m: m.count("warehouse.backfill.started", 1))
        self.assertFalse(msg["properties"]["$process_person_profile"])

    def test_attributes_cannot_rename_the_metric(self):
        msg = self.captured(
            lambda m: m.count(
                "real.name",
                1,
                attributes={"$metric_name": "spoofed", "$metric_kind": "gauge"},
            )
        )
        properties = msg["properties"]
        self.assertEqual(properties["$metric_name"], "real.name")
        self.assertEqual(properties["$metric_kind"], "count")

    def test_flush_drains_the_client(self):
        client = mock.MagicMock()
        InsightsMetrics(client).flush()
        client.flush.assert_called_once_with()
