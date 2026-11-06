import unittest

from shop.discount import apply_discount


class DiscountTest(unittest.TestCase):
    def test_save10(self):
        self.assertEqual(apply_discount(5000, "SAVE10"), 4500)

    def test_save25(self):
        self.assertEqual(apply_discount(2000, "SAVE25"), 1500)

    def test_lowercase_code(self):
        self.assertEqual(apply_discount(1000, "staff50"), 500)

    def test_unknown_code(self):
        with self.assertRaises(ValueError):
            apply_discount(1000, "FREE")
