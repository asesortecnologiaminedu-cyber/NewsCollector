from __future__ import annotations

import unittest

from newscollector.newscollector import Helper, NewsCollector, Processer, Scraper, _parse_bool


class NewsCollectorApiTests(unittest.TestCase):
    def test_newscollector_instantiates_with_custom_sources(self) -> None:
        collector = NewsCollector(
            sources="newscollector/sources.json",
            news_name="Test News",
            news_date="2026-05-26",
            auto_open=False,
            return_details=False,
        )

        self.assertIsInstance(collector, NewsCollector)
        self.assertEqual(collector.news_name, "Test News")

    def test_bool_parser_accepts_and_rejects_expected_values(self) -> None:
        self.assertTrue(_parse_bool("true"))
        self.assertFalse(_parse_bool("no"))

        with self.assertRaises(Exception):
            _parse_bool("not-a-bool")

    def test_legacy_exports_remain_available(self) -> None:
        self.assertTrue(hasattr(Helper, "clean_articles"))
        self.assertTrue(hasattr(Processer, "compute_tfidf"))
        self.assertTrue(hasattr(Scraper, "scrape"))


if __name__ == "__main__":
    unittest.main()
