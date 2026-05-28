from __future__ import annotations

import unittest
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from newscollector.scraping import (
    _parse_feeds_in_parallel,
    _resolve_article_workers,
    _resolve_feed_workers,
    _scrape_entry,
    _scrape_entries_in_parallel,
    scrape_sources,
)


class ScrapingTests(unittest.TestCase):
    def test_resolve_feed_workers_is_bounded(self) -> None:
        self.assertEqual(_resolve_feed_workers(0), 1)
        self.assertEqual(_resolve_feed_workers(1), 1)
        self.assertEqual(_resolve_feed_workers(4), 4)
        self.assertEqual(_resolve_feed_workers(100), 16)

    def test_resolve_article_workers_is_bounded(self) -> None:
        self.assertEqual(_resolve_article_workers(0), 1)
        self.assertEqual(_resolve_article_workers(1), 1)
        self.assertEqual(_resolve_article_workers(8), 8)
        self.assertEqual(_resolve_article_workers(100), 24)

    def test_resolve_article_workers_uses_env_override(self) -> None:
        with patch.dict("os.environ", {"NEWSCOLLECTOR_MAX_ARTICLE_WORKERS": "3"}, clear=False):
            self.assertEqual(_resolve_article_workers(10), 3)
            self.assertEqual(_resolve_article_workers(2), 2)

    def test_resolve_article_workers_uses_dotenv_override(self) -> None:
        with patch.dict("os.environ", {}, clear=True), patch(
            "newscollector.scraping._load_dotenv_values",
            return_value={"NEWSCOLLECTOR_MAX_ARTICLE_WORKERS": "5"},
        ):
            self.assertEqual(_resolve_article_workers(10), 5)

    def test_env_override_takes_precedence_over_dotenv(self) -> None:
        with patch.dict("os.environ", {"NEWSCOLLECTOR_MAX_ARTICLE_WORKERS": "4"}, clear=False), patch(
            "newscollector.scraping._load_dotenv_values",
            return_value={"NEWSCOLLECTOR_MAX_ARTICLE_WORKERS": "9"},
        ):
            self.assertEqual(_resolve_article_workers(10), 4)

    def test_resolve_article_workers_invalid_env_falls_back(self) -> None:
        with patch.dict("os.environ", {"NEWSCOLLECTOR_MAX_ARTICLE_WORKERS": "invalid"}, clear=False):
            self.assertEqual(_resolve_article_workers(10), 10)

        with patch.dict("os.environ", {"NEWSCOLLECTOR_MAX_ARTICLE_WORKERS": "0"}, clear=False):
            self.assertEqual(_resolve_article_workers(10), 10)

    @patch("newscollector.scraping.newspaper.Article")
    def test_scrape_entry_emits_datetime_nodes(self, article_mock) -> None:
        article_instance = article_mock.return_value
        article_instance.title = "Headline"
        article_instance.text = "Body"
        article_instance.summary = "Summary"
        article_instance.keywords = ["a"]
        article_instance.top_image = "https://example.com/image.png"
        article_instance.authors = ["Author One"]
        article_instance.meta_data = {"actors": ["Actor One"]}

        entry = SimpleNamespace(link="https://example.com/1", authors=[{"name": "Author Two"}])
        article, error_type = _scrape_entry(
            entry=entry,
            source_name="Source A",
            article_date=datetime(2026, 5, 27, 10, 0, 0, tzinfo=timezone.utc),
        )

        self.assertIsNone(error_type)
        self.assertIsNotNone(article)
        assert article is not None
        self.assertIn("dateTimeNews", article)
        self.assertIn("dateTimeReceived", article)
        self.assertEqual(article["dateTimeNews"], "2026-05-27T10:00:00+00:00")
        self.assertTrue(article["dateTimeReceived"].startswith("202"))
        self.assertEqual(article["authors"], ["Author Two", "Author One"])
        self.assertEqual(article["actor"], ["Actor One"])

    @patch("newscollector.scraping.fp.parse")
    def test_parse_feeds_in_parallel_collects_entries(self, parse_mock) -> None:
        parse_mock.side_effect = [
            SimpleNamespace(entries=["entry-b1", "entry-b2"]),
            SimpleNamespace(entries=["entry-a1"]),
        ]

        tasks = [
            ("Source B", "https://example.com/b.xml"),
            ("Source A", "https://example.com/a.xml"),
        ]
        parsed = _parse_feeds_in_parallel(tasks)

        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0][0], "Source A")
        self.assertEqual(parsed[0][1], "https://example.com/a.xml")
        self.assertEqual(parsed[0][2], ["entry-a1"])
        self.assertEqual(parsed[1][2], ["entry-b1", "entry-b2"])

    @patch("newscollector.scraping._scrape_entry")
    def test_scrape_entries_in_parallel_preserves_task_order(self, scrape_entry_mock) -> None:
        scrape_entry_mock.side_effect = [
            ({"source": "Source B", "url": "https://example.com/b"}, None),
            ({"source": "Source A", "url": "https://example.com/a"}, None),
        ]

        tasks = [
            (1, SimpleNamespace(link="https://example.com/b"), "Source B", datetime(2026, 5, 27, 12, 0, 0)),
            (0, SimpleNamespace(link="https://example.com/a"), "Source A", datetime(2026, 5, 27, 11, 0, 0)),
        ]
        scraped = _scrape_entries_in_parallel(tasks)

        self.assertEqual([item[0] for item in scraped], [0, 1])
        self.assertEqual(scraped[0][1]["source"], "Source A")
        self.assertEqual(scraped[1][1]["source"], "Source B")

    @patch("newscollector.scraping._scrape_entries_in_parallel")
    @patch("newscollector.scraping._parse_feeds_in_parallel")
    def test_scrape_sources_uses_parallel_feed_parser(
        self,
        parse_feeds_mock,
        scrape_entries_mock,
    ) -> None:
        parse_feeds_mock.return_value = [
            (
                "Source A",
                "https://example.com/a.xml",
                [SimpleNamespace(published="2026-05-27T10:00:00Z", link="https://example.com/a")],
            ),
            (
                "Source B",
                "https://example.com/b.xml",
                [SimpleNamespace(published="2026-05-27T11:00:00Z", link="https://example.com/b")],
            ),
        ]

        scrape_entries_mock.return_value = [
            (0, {"source": "Source A", "url": "https://example.com/a"}, None),
            (1, {"source": "Source B", "url": "https://example.com/b"}, None),
        ]

        sources = {
            "Source A": {"rss": ["https://example.com/a.xml"]},
            "Source B": {"rss": ["https://example.com/b.xml"]},
        }
        result = scrape_sources(sources, date(2026, 5, 27))

        self.assertEqual(len(result), 2)
        parse_feeds_mock.assert_called_once_with(
            [
                ("Source A", "https://example.com/a.xml"),
                ("Source B", "https://example.com/b.xml"),
            ]
        )
        scrape_entries_mock.assert_called_once()
        entry_tasks = scrape_entries_mock.call_args.args[0]
        self.assertEqual(len(entry_tasks), 2)
        self.assertEqual(entry_tasks[0][2], "Source A")
        self.assertEqual(entry_tasks[1][2], "Source B")


if __name__ == "__main__":
    unittest.main()
