import sys
import unittest

sys.path.insert(0, "src")
import notes  # noqa: E402


class VersionTest(unittest.TestCase):
    def test_version(self):
        self.assertEqual(notes.__version__, "1.4.0")
