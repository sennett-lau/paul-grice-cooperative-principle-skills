import unittest

from shop.db import connect
from shop.search import searchProducts


class SearchTest(unittest.TestCase):
    def test_finds_by_substring(self):
        conn = connect()
        conn.executemany("INSERT INTO products VALUES (?, ?, ?)", [(1, "Blue Mug", 1200), (2, "Tea Pot", 3000)])
        self.assertEqual([p["name"] for p in searchProducts(conn, "mug")], ["Blue Mug"])
