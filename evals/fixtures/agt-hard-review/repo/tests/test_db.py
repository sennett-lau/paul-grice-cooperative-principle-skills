import unittest

from shop.db import connect, get_product


class DbTest(unittest.TestCase):
    def test_get_product(self):
        conn = connect()
        conn.execute("INSERT INTO products VALUES (1, 'Mug', 1200)")
        self.assertEqual(get_product(conn, 1), (1, "Mug", 1200))
