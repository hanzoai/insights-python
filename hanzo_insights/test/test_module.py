import unittest

from hanzo_insights import Insights


class TestModule(unittest.TestCase):
    client = None

    def _assert_enqueue_result(self, result):
        self.assertEqual(type(result[0]), str)

    def failed(self):
        self.failed = True

    def setUp(self):
        self.failed = False
        self.client = Insights(
            "testsecret", host="http://localhost:8000", on_error=self.failed
        )

    def test_track(self):
        res = self.client.capture("python module event", distinct_id="distinct_id")
        self._assert_enqueue_result(res)
        self.client.flush()

    def test_alias(self):
        res = self.client.alias("previousId", "distinct_id")
        self._assert_enqueue_result(res)
        self.client.flush()

    def test_flush(self):
        self.client.flush()
