import unittest

from notes.cli import build_parser


class CliTest(unittest.TestCase):
    def test_default_server(self):
        self.assertEqual(build_parser().parse_args([]).server, "https://notes.acme.internal")
