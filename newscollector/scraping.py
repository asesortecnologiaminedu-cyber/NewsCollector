from __future__ import annotations

from datetime import date, datetime
from typing import Any

import dateutil
import feedparser as fp
import newspaper

try:
    from .logging_utils import log_info, log_warn, print_scrape_status
except ImportError:  # pragma: no cover - direct script execution support
    from logging_utils import log_info, log_warn, print_scrape_status

ArticleRecord = dict[str, Any]
SourcesMap = dict[str, dict[str, Any]]


def scrape_sources(sources: SourcesMap, news_date: date) -> list[ArticleRecord]:
    articles_list: list[ArticleRecord] = []
    stats = {
        "sources": 0,
        "rss_feeds": 0,
        "entries_seen": 0,
        "entries_with_published": 0,
        "entries_for_date": 0,
        "download_errors": 0,
        "article_errors": 0,
    }

    for source_name, source_content in sources.items():
        stats["sources"] += 1
        rss_urls = source_content.get("rss", [])
        if not isinstance(rss_urls, list):
            log_warn(f'Skipping source "{source_name}" because field "rss" is not a list.')
            continue

        log_info(f'Scraping source "{source_name}" with {len(rss_urls)} RSS feeds.')

        for feed_url in rss_urls:
            stats["rss_feeds"] += 1
            parsed_feed = fp.parse(feed_url)
            entries = getattr(parsed_feed, "entries", [])
            stats["entries_seen"] += len(entries)
            log_info(f"Feed {feed_url} returned {len(entries)} entries.")

            for entry in entries:
                published_value = getattr(entry, "published", None)
                if not published_value:
                    continue

                stats["entries_with_published"] += 1
                article_date = _parse_entry_date(published_value)
                if article_date is None:
                    continue

                if article_date.date() != news_date:
                    continue

                stats["entries_for_date"] += 1
                article, error_type = _scrape_entry(
                    entry=entry,
                    source_name=source_name,
                    article_date=article_date,
                )

                if article is None:
                    if error_type == "article":
                        stats["article_errors"] += 1
                    else:
                        stats["download_errors"] += 1
                    continue

                articles_list.append(article)
                print_scrape_status(len(articles_list))

    log_info(
        "Scrape summary: "
        f"sources={stats['sources']}, feeds={stats['rss_feeds']}, "
        f"entries={stats['entries_seen']}, published={stats['entries_with_published']}, "
        f"matching_date={stats['entries_for_date']}, collected={len(articles_list)}, "
        f"download_errors={stats['download_errors']}, article_errors={stats['article_errors']}"
    )
    return articles_list


def _parse_entry_date(published_value: str) -> datetime | None:
    try:
        return dateutil.parser.parse(published_value)
    except Exception as exc:
        log_warn(f'Could not parse article date "{published_value}": {exc}')
        return None


def _scrape_entry(
    entry: Any,
    source_name: str,
    article_date: datetime,
) -> tuple[ArticleRecord | None, str | None]:
    article_link = getattr(entry, "link", None)
    if not article_link:
        return None, "download"

    try:
        article_content = newspaper.Article(article_link)
        article_content.download()
        article_content.parse()
        article_content.nlp()
    except Exception as exc:
        log_warn(f"Failed to download/parse article {article_link}: {exc}")
        return None, "download"

    try:
        return {
            "source": source_name,
            "url": article_link,
            "date": article_date.strftime("%Y-%m-%d"),
            "time": article_date.strftime("%H:%M:%S %Z"),
            "title": article_content.title,
            "body": article_content.text,
            "summary": article_content.summary,
            "keywords": article_content.keywords,
            "image_url": article_content.top_image,
        }, None
    except Exception as exc:
        log_warn(f'Failed to map parsed article for source "{source_name}": {exc}')
        return None, "article"
