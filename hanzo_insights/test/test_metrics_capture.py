import gzip
import json
import unittest

import mock
from parameterized import parameterized

from hanzo_insights.client import Client
from hanzo_insights.metrics_capture import DEFAULT_HISTOGRAM_BOUNDS, InsightsMetrics
from hanzo_insights.test.test_utils import FAKE_TEST_API_KEY


class FakeClient:
    """The surface `InsightsMetrics` reads off the client."""

    def __init__(self, disabled=False, send=True):
        self.api_key = FAKE_TEST_API_KEY
        self.host = "https://us.i.insights.hanzo.ai"
        self.timeout = 15
        self.disabled = disabled
        self.send = send


def attributes_of(data_point):
    return {
        item["key"]: list(item["value"].values())[0]
        for item in data_point["attributes"]
    }


class MetricsTestCase(unittest.TestCase):
    def setUp(self):
        self.client = FakeClient()
        self.metrics = InsightsMetrics(self.client)

    def tearDown(self):
        self.metrics.reset()

    def flush(self, status_code=200):
        """Flush against a mocked transport, return the decoded request body (None if nothing was sent)."""
        with mock.patch("hanzo_insights.metrics_capture._get_session") as get_session:
            post = get_session.return_value.post
            post.return_value.status_code = status_code
            self.metrics.flush()
            self.post = post
            if not post.called:
                return None
            return json.loads(gzip.decompress(post.call_args[1]["data"]))

    def sent_metrics(self, status_code=200):
        payload = self.flush(status_code)
        self.assertIsNotNone(payload)
        return payload["resourceMetrics"][0]["scopeMetrics"][0]["metrics"]

    def one_metric(self, status_code=200):
        metrics = self.sent_metrics(status_code)
        self.assertEqual(len(metrics), 1)
        return metrics[0]


class TestAggregation(MetricsTestCase):
    def test_counts_sum_into_one_data_point(self):
        for value in (1, 2, 3):
            self.metrics.count("invoices.processed", value, attributes={"plan": "pro"})

        data_points = self.one_metric()["sum"]["dataPoints"]
        self.assertEqual(len(data_points), 1)
        self.assertEqual(data_points[0]["asDouble"], 6.0)

    def test_gauge_keeps_the_last_value(self):
        for value in (42, 7, 13):
            self.metrics.gauge("queue.depth", value)

        data_points = self.one_metric()["gauge"]["dataPoints"]
        self.assertEqual(len(data_points), 1)
        self.assertEqual(data_points[0]["asDouble"], 13.0)

    def test_histogram_accumulates_buckets(self):
        # 3 -> bucket 1 (<= 5), 7 -> bucket 2 (<= 10), 20000 -> the overflow bucket.
        for value in (3, 7, 20000):
            self.metrics.histogram("job.duration", value, unit="ms")

        data_points = self.one_metric()["histogram"]["dataPoints"]
        self.assertEqual(len(data_points), 1)
        point = data_points[0]
        self.assertEqual(point["count"], 3)
        self.assertEqual(point["sum"], 20010.0)
        self.assertEqual(point["min"], 3.0)
        self.assertEqual(point["max"], 20000.0)
        expected_buckets = [0] * (len(DEFAULT_HISTOGRAM_BOUNDS) + 1)
        expected_buckets[1] = 1
        expected_buckets[2] = 1
        expected_buckets[-1] = 1
        self.assertEqual(point["bucketCounts"], expected_buckets)

    def test_attributes_form_the_series_key(self):
        self.metrics.count("invoices.processed", 1, attributes={"plan": "pro"})
        self.metrics.count("invoices.processed", 1, attributes={"plan": "free"})
        self.metrics.count("invoices.processed", 4, attributes={"plan": "pro"})

        data_points = self.one_metric()["sum"]["dataPoints"]
        by_plan = {
            attributes_of(point)["plan"]: point["asDouble"] for point in data_points
        }
        self.assertEqual(by_plan, {"pro": 5.0, "free": 1.0})

    def test_attribute_order_does_not_split_the_series(self):
        self.metrics.count("jobs.run", 1, attributes={"a": "1", "b": "2"})
        self.metrics.count("jobs.run", 1, attributes={"b": "2", "a": "1"})

        data_points = self.one_metric()["sum"]["dataPoints"]
        self.assertEqual(len(data_points), 1)
        self.assertEqual(data_points[0]["asDouble"], 2.0)

    def test_none_valued_attributes_are_stripped_from_the_series(self):
        self.metrics.count("jobs.run", 1, attributes={"dataset": "events"})
        self.metrics.count(
            "jobs.run", 1, attributes={"dataset": "events", "mode": None}
        )

        data_points = self.one_metric()["sum"]["dataPoints"]
        self.assertEqual(len(data_points), 1)
        self.assertEqual(data_points[0]["asDouble"], 2.0)
        self.assertEqual(attributes_of(data_points[0]), {"dataset": "events"})

    def test_mutating_the_attributes_afterwards_does_not_change_the_series(self):
        attributes = {"dataset": "events"}
        self.metrics.count("jobs.run", 1, attributes=attributes)
        attributes["dataset"] = "persons"

        data_points = self.one_metric()["sum"]["dataPoints"]
        self.assertEqual(attributes_of(data_points[0]), {"dataset": "events"})

    def test_the_kind_separates_series_of_the_same_name(self):
        self.metrics.count("backfill.rows", 1)
        self.metrics.gauge("backfill.rows", 5)

        metrics = self.sent_metrics()
        self.assertEqual({metric["name"] for metric in metrics}, {"backfill.rows"})
        kinds = sorted(key for metric in metrics for key in metric if key != "name")
        self.assertEqual(kinds, ["gauge", "sum"])


class TestPayload(MetricsTestCase):
    def test_count_data_point(self):
        self.metrics.count("invoices.processed", 2, attributes={"plan": "pro"})

        metric = self.one_metric()
        self.assertEqual(metric["name"], "invoices.processed")
        self.assertNotIn("unit", metric)
        self.assertTrue(metric["sum"]["isMonotonic"])
        point = metric["sum"]["dataPoints"][0]
        self.assertEqual(point["asDouble"], 2.0)
        self.assertEqual(
            point["attributes"], [{"key": "plan", "value": {"stringValue": "pro"}}]
        )
        self.assertTrue(point["startTimeUnixNano"].endswith("000000"))
        self.assertTrue(point["timeUnixNano"].endswith("000000"))
        self.assertGreaterEqual(
            int(point["timeUnixNano"]), int(point["startTimeUnixNano"])
        )

    def test_gauge_data_point_has_no_start_time(self):
        self.metrics.gauge("queue.depth", 42, unit="1")

        metric = self.one_metric()
        self.assertEqual(metric["unit"], "1")
        self.assertEqual(list(metric["gauge"].keys()), ["dataPoints"])
        point = metric["gauge"]["dataPoints"][0]
        self.assertEqual(point["asDouble"], 42.0)
        self.assertNotIn("startTimeUnixNano", point)

    def test_histogram_data_point_carries_the_default_bounds(self):
        self.metrics.histogram("job.duration", 187, unit="ms")

        metric = self.one_metric()
        self.assertEqual(metric["unit"], "ms")
        point = metric["histogram"]["dataPoints"][0]
        self.assertEqual(point["explicitBounds"], DEFAULT_HISTOGRAM_BOUNDS)
        # count and bucketCounts are plain JSON numbers, not decimal strings.
        self.assertIsInstance(point["count"], int)
        self.assertTrue(all(isinstance(n, int) for n in point["bucketCounts"]))

    @parameterized.expand([("count", "sum"), ("histogram", "histogram")])
    def test_delta_temporality(self, method, field):
        getattr(self.metrics, method)("jobs.run", 1)

        self.assertEqual(self.one_metric()[field]["aggregationTemporality"], 1)

    def test_gauges_carry_no_temporality(self):
        self.metrics.gauge("queue.depth", 1)

        self.assertNotIn("aggregationTemporality", self.one_metric()["gauge"])

    def test_resource_and_scope_identify_the_sdk(self):
        self.metrics = InsightsMetrics(
            self.client, {"service_name": "billing-worker", "environment": "prod"}
        )
        self.metrics.count("invoices.processed", 1)

        payload = self.flush()
        resource = payload["resourceMetrics"][0]
        attributes = {
            item["key"]: list(item["value"].values())[0]
            for item in resource["resource"]["attributes"]
        }
        self.assertEqual(attributes["service.name"], "billing-worker")
        self.assertEqual(attributes["deployment.environment"], "prod")
        self.assertEqual(attributes["telemetry.sdk.name"], "insights-python")
        self.assertEqual(
            resource["scopeMetrics"][0]["scope"]["name"], "insights-python"
        )

    @parameterized.expand(
        [
            ("string", "events", {"stringValue": "events"}),
            ("bool", True, {"boolValue": True}),
            ("int", 7, {"intValue": 7}),
            ("integral_float", 7.0, {"intValue": 7}),
            ("float", 7.5, {"doubleValue": 7.5}),
        ]
    )
    def test_attribute_value_encoding(self, _name, value, expected):
        self.metrics.count("jobs.run", 1, attributes={"key": value})

        point = self.one_metric()["sum"]["dataPoints"][0]
        self.assertEqual(point["attributes"], [{"key": "key", "value": expected}])

    def test_request_is_gzipped_json_to_the_metrics_endpoint(self):
        self.metrics.count("jobs.run", 1)
        self.flush()

        url = self.post.call_args[0][0]
        self.assertEqual(
            url,
            "https://us.i.insights.hanzo.ai/i/v1/metrics?token=" + FAKE_TEST_API_KEY,
        )
        self.assertEqual(
            self.post.call_args[1]["headers"],
            {"Content-Type": "application/json", "Content-Encoding": "gzip"},
        )


class TestFlush(MetricsTestCase):
    def test_flush_takes_no_arguments_and_empties_the_window(self):
        self.metrics.count("jobs.run", 1)

        self.assertIsNotNone(self.flush())
        self.assertIsNone(self.flush())

    def test_nothing_recorded_sends_nothing(self):
        self.assertIsNone(self.flush())

    def test_a_failed_flush_rides_the_next_window(self):
        self.metrics.count("jobs.run", 2)
        self.flush(status_code=500)

        self.metrics.count("jobs.run", 3)
        point = self.one_metric()["sum"]["dataPoints"][0]
        self.assertEqual(point["asDouble"], 5.0)

    def test_a_rejected_batch_is_dropped(self):
        self.metrics.count("jobs.run", 2)
        self.flush(status_code=413)

        self.assertIsNone(self.flush())

    def test_a_disabled_client_records_nothing(self):
        self.metrics = InsightsMetrics(FakeClient(disabled=True))
        self.metrics.count("jobs.run", 1)

        self.assertIsNone(self.flush())

    def test_send_false_discards_the_window(self):
        self.metrics = InsightsMetrics(FakeClient(send=False))
        self.metrics.count("jobs.run", 1)

        self.assertIsNone(self.flush())


class TestClientWiring(unittest.TestCase):
    def tearDown(self):
        self.client.shutdown()

    def test_metrics_is_lazy_and_cached(self):
        self.client = Client(FAKE_TEST_API_KEY)

        self.assertIsNone(self.client._metrics)
        self.assertIsInstance(self.client.metrics, InsightsMetrics)
        self.assertIs(self.client.metrics, self.client.metrics)

    def test_the_metrics_option_configures_the_service(self):
        self.client = Client(FAKE_TEST_API_KEY, metrics={"service_name": "warehouse"})
        self.client.metrics.count("jobs.run", 1)

        with mock.patch("hanzo_insights.metrics_capture._get_session") as get_session:
            get_session.return_value.post.return_value.status_code = 200
            self.client.metrics.flush()
            payload = json.loads(
                gzip.decompress(get_session.return_value.post.call_args[1]["data"])
            )

        attributes = payload["resourceMetrics"][0]["resource"]["attributes"]
        self.assertIn(
            {"key": "service.name", "value": {"stringValue": "warehouse"}}, attributes
        )

    def test_an_invalid_metrics_option_degrades_to_defaults(self):
        self.client = Client(FAKE_TEST_API_KEY, metrics="not a dict")

        self.assertIsInstance(self.client.metrics, InsightsMetrics)
        self.assertEqual(self.client.metrics._flush_interval, 10.0)

    def test_shutdown_flushes_pending_metrics(self):
        self.client = Client(FAKE_TEST_API_KEY)
        self.client.metrics.count("jobs.run", 1)

        with mock.patch("hanzo_insights.metrics_capture._get_session") as get_session:
            get_session.return_value.post.return_value.status_code = 200
            self.client.shutdown()
            get_session.return_value.post.assert_called_once()
