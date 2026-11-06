import unittest

from textutils.slug import slugify, truncate


class SlugifyTest(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_punctuation(self):
        self.assertEqual(slugify("What's new?"), "what-s-new")

    def test_numbers(self):
        self.assertEqual(slugify("Top 10 Tips"), "top-10-tips")

    def test_unicode(self):
        self.assertEqual(slugify("Crème Brûlée"), "creme-brulee")


class TruncateTest(unittest.TestCase):
    def test_short(self):
        self.assertEqual(truncate("abc", 5), "abc")

    def test_exact(self):
        self.assertEqual(truncate("abcde", 5), "abcde")

    def test_cut(self):
        self.assertEqual(truncate("hello world", 6), "hello…")

    def test_cut_strips_space(self):
        self.assertEqual(truncate("hello world", 7), "hello…")
