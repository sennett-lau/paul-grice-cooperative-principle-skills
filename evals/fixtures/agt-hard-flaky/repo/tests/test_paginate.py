import unittest

from reports.paginate import paginate


class PaginateTest(unittest.TestCase):
    def test_first_page(self):
        r = paginate(list(range(45)), 1)
        self.assertEqual(r["items"], list(range(20)))
        self.assertEqual(r["pages"], 3)

    def test_last_page(self):
        self.assertEqual(paginate(list(range(45)), 3)["items"], list(range(40, 45)))

    def test_empty(self):
        self.assertEqual(paginate([], 1), {"items": [], "page": 1, "pages": 1})

    def test_bad_page(self):
        with self.assertRaises(ValueError):
            paginate([1], 0)
