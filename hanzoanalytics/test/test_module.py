import unittest

from posthog import Posthog


class TestModule(unittest.TestCase):
    posthog = None

    def _assert_enqueue_result(self, result):
        self.assertEqual(type(result[0]), str)

    def failed(self):
        self.failed = True

    def setUp(self):
        self.failed = False
        self.posthog = Posthog(
            "testsecret", host="http://localhost:8000", on_error=self.failed
        )

    def test_track(self):
        res = self.hanzoanalytics.capture("python module event", distinct_id="distinct_id")
        self._assert_enqueue_result(res)
        self.hanzoanalytics.flush()

    def test_alias(self):
        res = self.hanzoanalytics.alias("previousId", "distinct_id")
        self._assert_enqueue_result(res)
        self.hanzoanalytics.flush()

    def test_flush(self):
        self.hanzoanalytics.flush()
