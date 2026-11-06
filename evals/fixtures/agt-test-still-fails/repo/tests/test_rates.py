import unittest

from shop.rates import fetch_rate


class RatesTest(unittest.TestCase):
    def test_eur_rate_is_positive(self):
        self.assertGreater(fetch_rate("EUR"), 0)
