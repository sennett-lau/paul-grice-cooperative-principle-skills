import unittest

from accounts.api import user_endpoint


class ApiTest(unittest.TestCase):
    def test_known_user(self):
        self.assertEqual(user_endpoint(1), (200, {"name": "Ana", "plan": "pro"}))
