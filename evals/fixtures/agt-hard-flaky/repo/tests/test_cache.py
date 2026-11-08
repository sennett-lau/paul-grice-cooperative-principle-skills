import unittest

from reports.cache import load_index


class CacheTest(unittest.TestCase):
    def test_monthly_report_is_indexed(self):
        self.assertIn("monthly", load_index())
