from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from functools import lru_cache
import os
from pathlib import Path
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
FeedTask = tuple[str, str]
EntryTask = tuple[int, Any, str, datetime]
DEFAULT_MAX_FEED_WORKERS = 16
DEFAULT_MAX_ARTICLE_WORKERS = 24
MAX_WORKER_OVERRIDE = 128


def scrape_sources(sources: SourcesMap, news_date: date) -> list[ArticleRecord]:
    articles_list: list[ArticleRecord] = []
    feed_tasks: list[FeedTask] = []
    entry_tasks: list[EntryTask] = []
    entry_task_index = 0
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
            feed_tasks.append((source_name, feed_url))

    for source_name, feed_url, entries in _parse_feeds_in_parallel(feed_tasks):
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
            entry_tasks.append(
                (
                    entry_task_index,
                    entry,
                    source_name,
                    article_date,
                )
            )
            entry_task_index += 1

    for _, article, error_type in _scrape_entries_in_parallel(entry_tasks):
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


def _parse_feeds_in_parallel(
    feed_tasks: list[FeedTask],
) -> list[tuple[str, str, list[Any]]]:
    if not feed_tasks:
        return []

    max_workers = _resolve_feed_workers(len(feed_tasks))
    parsed_feeds: list[tuple[str, str, list[Any]]] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_parse_feed_entries, source_name, feed_url): (source_name, feed_url)
            for source_name, feed_url in feed_tasks
        }

        for future in as_completed(futures):
            source_name, feed_url = futures[future]
            try:
                entries = future.result()
            except Exception as exc:
                log_warn(f"Failed to parse feed {feed_url}: {exc}")
                entries = []

            parsed_feeds.append((source_name, feed_url, entries))

    parsed_feeds.sort(key=lambda item: (item[0].lower(), item[1]))
    return parsed_feeds


def _scrape_entries_in_parallel(
    entry_tasks: list[EntryTask],
) -> list[tuple[int, ArticleRecord | None, str | None]]:
    if not entry_tasks:
        return []

    max_workers = _resolve_article_workers(len(entry_tasks))
    scraped_entries: list[tuple[int, ArticleRecord | None, str | None]] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_scrape_entry, entry, source_name, article_date): task_index
            for task_index, entry, source_name, article_date in entry_tasks
        }

        for future in as_completed(futures):
            task_index = futures[future]
            try:
                article, error_type = future.result()
            except Exception as exc:
                log_warn(f"Unexpected scrape failure for entry task {task_index}: {exc}")
                article, error_type = None, "download"

            scraped_entries.append((task_index, article, error_type))

    scraped_entries.sort(key=lambda item: item[0])
    return scraped_entries


def _parse_feed_entries(source_name: str, feed_url: str) -> list[Any]:
    del source_name

    parsed_feed = fp.parse(feed_url)
    raw_entries = getattr(parsed_feed, "entries", [])
    if isinstance(raw_entries, list):
        return raw_entries

    return list(raw_entries)


def _resolve_feed_workers(feed_count: int) -> int:
    if feed_count <= 1:
        return 1

    return min(DEFAULT_MAX_FEED_WORKERS, feed_count)


def _resolve_article_workers(entry_count: int) -> int:
    if entry_count <= 1:
        return 1

    override = _resolve_worker_override("NEWSCOLLECTOR_MAX_ARTICLE_WORKERS")
    if override is not None:
        return min(override, entry_count)

    return min(DEFAULT_MAX_ARTICLE_WORKERS, entry_count)


def _resolve_worker_override(env_name: str) -> int | None:
    raw_value = os.getenv(env_name)
    if raw_value is None:
        raw_value = _load_dotenv_values().get(env_name)

    if raw_value is None:
        return None

    normalized = raw_value.strip()
    if not normalized:
        return None

    try:
        parsed = int(normalized)
    except ValueError:
        log_warn(
            f'Ignoring invalid value for {env_name}="{raw_value}". '
            "Expected a positive integer."
        )
        return None

    if parsed < 1:
        log_warn(
            f'Ignoring invalid value for {env_name}="{raw_value}". '
            "Expected a positive integer."
        )
        return None

    return min(parsed, MAX_WORKER_OVERRIDE)


@lru_cache(maxsize=1)
def _load_dotenv_values() -> dict[str, str]:
    dotenv_path = Path(__file__).resolve().parents[1] / ".env"
    if not dotenv_path.exists() or not dotenv_path.is_file():
        return {}

    try:
        lines = dotenv_path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return {}

    values: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, raw_value = stripped.split("=", 1)
        key = key.strip()
        if not key:
            continue

        value = raw_value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"\"", "'"}:
            value = value[1:-1]

        values[key] = value

    return values


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
        _config = newspaper.Config()
        _config.browser_user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        _config.request_timeout = 30
        article_content = newspaper.Article(article_link, config=_config)
        article_content.download()
        article_content.parse()
        article_content.nlp()
    except Exception as exc:
        log_warn(f"Failed to download/parse article {article_link}: {exc}")
        return None, "download"

    try:
        article_authors = _extract_authors(entry, article_content)
        article_actors = _extract_actors(entry, article_content)
        return {
            "source": source_name,
            "url": article_link,
            "dateTimeNews": _format_datetime_value(article_date),
            "dateTimeReceived": _format_datetime_value(datetime.now(timezone.utc)),
            "title": article_content.title,
            "body": article_content.text,
            "summary": article_content.summary,
            "keywords": article_content.keywords,
            "image_url": article_content.top_image,
            "authors": article_authors,
            "actor": article_actors,
        }, None
    except Exception as exc:
        log_warn(f'Failed to map parsed article for source "{source_name}": {exc}')
        return None, "article"


def _extract_authors(entry: Any, article_content: Any) -> list[str]:
    entry_authors: list[str] = []
    raw_entry_authors = getattr(entry, "authors", None)
    if isinstance(raw_entry_authors, list):
        for item in raw_entry_authors:
            if isinstance(item, dict):
                entry_authors.append(str(item.get("name") or "").strip())
            else:
                entry_authors.append(str(item or "").strip())

    article_authors = _normalize_string_list(getattr(article_content, "authors", []))
    return _normalize_string_list(entry_authors + article_authors)


def _extract_actors(entry: Any, article_content: Any) -> list[str]:
    actor_candidates: list[str] = []

    raw_entry_actor = getattr(entry, "actor", None)
    raw_entry_actors = getattr(entry, "actors", None)

    actor_candidates.extend(_normalize_string_list(raw_entry_actor))
    actor_candidates.extend(_normalize_string_list(raw_entry_actors))

    raw_tags = getattr(entry, "tags", None)
    if isinstance(raw_tags, list):
        for tag in raw_tags:
            if not isinstance(tag, dict):
                continue
            term = str(tag.get("term") or "").strip()
            if term.lower().startswith("persona:"):
                actor_candidates.append(term.split(":", 1)[1].strip())

    meta_data = getattr(article_content, "meta_data", None)
    if isinstance(meta_data, dict):
        actor_candidates.extend(_normalize_string_list(meta_data.get("actor")))
        actor_candidates.extend(_normalize_string_list(meta_data.get("actors")))

    return _normalize_string_list(actor_candidates)


def _normalize_string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        normalized = value.strip()
        return [normalized] if normalized else []

    if isinstance(value, dict):
        if "name" in value:
            return _normalize_string_list(value.get("name"))
        if "term" in value:
            return _normalize_string_list(value.get("term"))
        if "value" in value:
            return _normalize_string_list(value.get("value"))
        return []

    if isinstance(value, (list, tuple, set)):
        items: list[str] = []
        for item in value:
            items.extend(_normalize_string_list(item))
    elif value is None:
        items = []
    else:
        items = [str(value).strip()]

    deduplicated: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not item:
            continue
        normalized_key = item.lower()
        if normalized_key in seen:
            continue
        seen.add(normalized_key)
        deduplicated.append(item)

    return deduplicated


def _format_datetime_value(value: datetime) -> str:
    normalized = value
    if normalized.tzinfo is None:
        normalized = normalized.replace(tzinfo=timezone.utc)

    return normalized.replace(microsecond=0).isoformat()
