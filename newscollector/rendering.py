from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Any

import flask

try:
    from .logging_utils import log_info
    from .processing import Clusters, shuffle_content
except ImportError:  # pragma: no cover - direct script execution support
    from logging_utils import log_info
    from processing import Clusters, shuffle_content

REPORT_SCHEMA_VERSION = "1.1"


def build_html(
    clusters_dict: Clusters,
    news_name: str,
    news_date: date | str,
    template: str,
    output_filename: str,
    template_path: str,
) -> bool:
    output_paths = build_outputs(
        clusters_dict=clusters_dict,
        news_name=news_name,
        news_date=news_date,
        template=template,
        output_filename=output_filename,
        template_path=template_path,
    )
    log_info(
        "Wrote consolidated newsletter outputs to "
        f'{output_paths["html"]}, {output_paths["markdown"]}, {output_paths["json"]}'
    )
    return True


def build_outputs(
    clusters_dict: Clusters,
    news_name: str,
    news_date: date | str,
    template: str,
    output_filename: str,
    template_path: str,
) -> dict[str, str]:
    newsletter_app = flask.Flask("newsletter", template_folder=template_path)
    output_paths = _resolve_output_paths(output_filename)

    shuffle_content(clusters_dict)
    consolidated_report = _build_consolidated_report(
        clusters_dict=clusters_dict,
        news_name=news_name,
        news_date=news_date,
    )
    canonical_report = _canonicalize_report(consolidated_report)
    merged_report = _merge_with_existing_report(canonical_report, output_paths["json"])

    log_info(
        "Rendering newsletter with "
        f'{len(merged_report["clusters"])} cards using template "{template}".'
    )

    _write_json_report(merged_report, output_paths["json"])
    _write_html_report(
        newsletter_app=newsletter_app,
        canonical_report=merged_report,
        template=template,
        output_filename=output_paths["html"],
    )
    _write_markdown_report(merged_report, output_paths["markdown"])

    return output_paths


def _write_html_report(
    newsletter_app: flask.Flask,
    canonical_report: dict[str, Any],
    template: str,
    output_filename: str,
) -> None:
    logo_path = _resolve_logo_path(output_filename)

    with newsletter_app.app_context():
        rendered = flask.render_template(
            template,
            news_name=canonical_report["news_name"],
            news_date=canonical_report["news_date"],
            clusters=canonical_report["clusters"],
            logo_path=logo_path,
        )

    Path(output_filename).write_text(rendered, encoding="utf-8")


def _write_markdown_report(canonical_report: dict[str, Any], output_filename: str) -> None:
    markdown_text = _render_markdown_report(canonical_report)
    Path(output_filename).write_text(markdown_text, encoding="utf-8")


def _write_json_report(canonical_report: dict[str, Any], output_filename: str) -> None:
    serialized_report = json.dumps(canonical_report, ensure_ascii=False, indent=2)
    Path(output_filename).write_text(f"{serialized_report}\n", encoding="utf-8")


def _canonicalize_report(report: dict[str, Any]) -> dict[str, Any]:
    serialized_report = json.dumps(report, ensure_ascii=False)
    return json.loads(serialized_report)


def _resolve_output_paths(output_filename: str) -> dict[str, str]:
    html_path = Path(output_filename)
    markdown_path = _derive_sibling_output(html_path, ".md")
    json_path = _derive_sibling_output(html_path, ".json")

    for output_path in (html_path, markdown_path, json_path):
        output_path.parent.mkdir(parents=True, exist_ok=True)

    return {
        "html": str(html_path),
        "markdown": str(markdown_path),
        "json": str(json_path),
    }


def _derive_sibling_output(output_path: Path, suffix: str) -> Path:
    candidate = output_path.with_suffix(suffix)
    if candidate == output_path:
        candidate = output_path.with_name(f"{output_path.stem}_report{suffix}")
    return candidate


def _render_markdown_report(canonical_report: dict[str, Any]) -> str:
    lines = [
        f"# {canonical_report['news_name']}",
        "",
        f"Fecha: {canonical_report['news_date']}",
        "",
    ]

    clusters = canonical_report.get("clusters", [])
    if not clusters:
        lines.append("_No hay noticias disponibles._")
        lines.append("")
        return "\n".join(lines)

    for cluster in clusters:
        position = cluster.get("position", "")
        title = cluster.get("title", "")
        source = cluster.get("source", "")
        url = cluster.get("url", "")
        pic = cluster.get("pic", "")
        authors = _normalize_text_list(cluster.get("authors") or cluster.get("author"))
        actors = _normalize_text_list(cluster.get("actor") or cluster.get("actors"))
        cluster_date = cluster.get("date", "")
        cluster_time = cluster.get("time", "")
        body = cluster.get("body", "")
        similar = cluster.get("similar", [])

        lines.append(f"## {position}. {title}")
        if cluster_date:
            lines.append(f"- Fecha: {cluster_date}")
        if cluster_time:
            lines.append(f"- Hora: {cluster_time}")
        lines.append(f"- Fuente: {source}")
        lines.append(f"- URL: {url}")
        if authors:
            lines.append(f"- Autores: {', '.join(authors)}")
        if actors:
            lines.append(f"- Actores: {', '.join(actors)}")
        if pic:
            lines.append(f"- Imagen: {pic}")
        lines.append("")

        if body:
            lines.append(str(body))
            lines.append("")

        if isinstance(similar, list) and similar:
            lines.append("Cobertura similar:")
            for similar_article in similar:
                if not isinstance(similar_article, dict):
                    continue
                similar_source = similar_article.get("source", "")
                similar_url = similar_article.get("url", "")
                lines.append(f"- {similar_source}: {similar_url}")
            lines.append("")

    return "\n".join(lines)


def _build_consolidated_report(
    clusters_dict: Clusters,
    news_name: str,
    news_date: date | str,
) -> dict[str, Any]:
    template_clusters = _build_template_clusters(clusters_dict)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "news_name": str(news_name),
        "news_date": str(news_date),
        "clusters": template_clusters,
    }


def _build_template_clusters(clusters_dict: Clusters) -> list[dict[str, Any]]:
    template_clusters: list[dict[str, Any]] = []

    for cluster_index in list(clusters_dict):
        articles = clusters_dict[cluster_index]
        if not articles:
            continue

        main_article = articles[0]
        cluster_data = {
            "position": len(template_clusters) + 1,
            "date": _get_article_field(main_article, "date"),
            "time": _get_article_field(main_article, "time"),
            "source": _get_article_field(main_article, "source"),
            "url": _get_article_field(main_article, "url"),
            "pic": _get_article_field(main_article, "image_url"),
            "title": _get_article_field(main_article, "title"),
            "body": _get_article_field(main_article, "body"),
            "authors": _get_article_list_field(main_article, "authors"),
            "actor": _get_article_list_field(main_article, "actor"),
            "similar": [],
        }

        for similar_article in articles[1:]:
            cluster_data["similar"].append(
                {
                    "source": _get_article_field(similar_article, "source"),
                    "url": _get_article_field(similar_article, "url"),
                }
            )

        template_clusters.append(cluster_data)

    return template_clusters


def _get_article_field(article: Any, field: str) -> str:
    try:
        if hasattr(article, "get"):
            value = article.get(field, "")
        else:
            value = article[field]
    except Exception:
        value = ""

    return str(value or "").strip()


def _get_article_list_field(article: Any, field: str) -> list[str]:
    try:
        if hasattr(article, "get"):
            value = article.get(field, [])
        else:
            value = article[field]
    except Exception:
        value = []

    return _normalize_text_list(value)


def _merge_with_existing_report(
    incoming_report: dict[str, Any],
    existing_report_path: str,
) -> dict[str, Any]:
    normalized_incoming = _normalize_report(incoming_report)
    existing_report = _load_existing_report(existing_report_path)
    if existing_report is None:
        return normalized_incoming

    normalized_existing = _normalize_report(existing_report)
    merged_clusters = _merge_clusters(
        normalized_existing.get("clusters", []),
        normalized_incoming.get("clusters", []),
    )

    merged_news_name = normalized_incoming["news_name"] or normalized_existing["news_name"]
    merged_news_date = normalized_incoming["news_date"] or normalized_existing["news_date"]

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "news_name": merged_news_name,
        "news_date": merged_news_date,
        "clusters": merged_clusters,
    }


def _load_existing_report(existing_report_path: str) -> dict[str, Any] | None:
    json_path = Path(existing_report_path)
    if not json_path.exists() or not json_path.is_file():
        return None

    try:
        loaded = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception:
        return None

    if not isinstance(loaded, dict):
        return None

    return loaded


def _normalize_report(report: dict[str, Any]) -> dict[str, Any]:
    news_name = _normalize_text(report.get("news_name"))
    news_date = _normalize_text(report.get("news_date"))
    raw_clusters = report.get("clusters")

    normalized_clusters: list[dict[str, Any]] = []
    if isinstance(raw_clusters, list):
        for raw_cluster in raw_clusters:
            if not isinstance(raw_cluster, dict):
                continue
            normalized_clusters.append(_normalize_cluster(raw_cluster, fallback_news_date=news_date))

    deduplicated = _deduplicate_clusters(normalized_clusters)
    ordered = _sort_clusters(deduplicated)
    positioned = _apply_positions(ordered)

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "news_name": news_name,
        "news_date": news_date,
        "clusters": positioned,
    }


def _normalize_cluster(cluster: dict[str, Any], fallback_news_date: str) -> dict[str, Any]:
    normalized_date = _normalize_text(cluster.get("date")) or fallback_news_date
    normalized_time = _normalize_time(cluster.get("time"))

    normalized_cluster = {
        "position": 0,
        "date": normalized_date,
        "time": normalized_time,
        "source": _normalize_text(cluster.get("source")),
        "url": _normalize_text(cluster.get("url")),
        "pic": _normalize_text(cluster.get("pic") or cluster.get("image_url")),
        "title": _normalize_text(cluster.get("title")),
        "body": _normalize_text(cluster.get("body")),
        "authors": _normalize_text_list(cluster.get("authors") or cluster.get("author")),
        "actor": _normalize_text_list(cluster.get("actor") or cluster.get("actors")),
        "similar": _normalize_similar_entries(cluster.get("similar")),
    }
    return normalized_cluster


def _normalize_similar_entries(raw_similar: Any) -> list[dict[str, str]]:
    if not isinstance(raw_similar, list):
        return []

    normalized_entries: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for entry in raw_similar:
        if not isinstance(entry, dict):
            continue

        source = _normalize_text(entry.get("source"))
        url = _normalize_text(entry.get("url"))
        if not source and not url:
            continue

        dedupe_key = (source.lower(), url.lower())
        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)
        normalized_entries.append({
            "source": source,
            "url": url,
        })

    return normalized_entries


def _merge_clusters(
    existing_clusters: list[dict[str, Any]],
    incoming_clusters: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_identity: dict[tuple[str, ...], dict[str, Any]] = {}

    for cluster in existing_clusters:
        identity = _cluster_identity_key(cluster)
        by_identity[identity] = dict(cluster)

    for cluster in incoming_clusters:
        identity = _cluster_identity_key(cluster)
        current = by_identity.get(identity)
        if current is None:
            by_identity[identity] = dict(cluster)
            continue

        by_identity[identity] = _merge_cluster_values(current, cluster)

    deduplicated = _deduplicate_clusters(list(by_identity.values()))
    ordered = _sort_clusters(deduplicated)
    return _apply_positions(ordered)


def _merge_cluster_values(
    existing_cluster: dict[str, Any],
    incoming_cluster: dict[str, Any],
) -> dict[str, Any]:
    merged_cluster = dict(existing_cluster)

    for field in ("date", "time", "source", "url", "pic", "title", "body"):
        incoming_value = _normalize_text(incoming_cluster.get(field))
        if incoming_value:
            merged_cluster[field] = incoming_value

    existing_similar = existing_cluster.get("similar")
    incoming_similar = incoming_cluster.get("similar")
    merged_similar_entries: list[Any] = []
    if isinstance(existing_similar, list):
        merged_similar_entries.extend(existing_similar)
    if isinstance(incoming_similar, list):
        merged_similar_entries.extend(incoming_similar)

    merged_cluster["similar"] = _normalize_similar_entries(merged_similar_entries)
    merged_cluster["authors"] = _merge_text_lists(
        existing_cluster.get("authors"),
        incoming_cluster.get("authors"),
    )
    merged_cluster["actor"] = _merge_text_lists(
        existing_cluster.get("actor") or existing_cluster.get("actors"),
        incoming_cluster.get("actor") or incoming_cluster.get("actors"),
    )
    return merged_cluster


def _deduplicate_clusters(clusters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduplicated: dict[tuple[str, ...], dict[str, Any]] = {}
    for cluster in clusters:
        identity = _cluster_identity_key(cluster)
        current = deduplicated.get(identity)
        if current is None:
            deduplicated[identity] = dict(cluster)
        else:
            deduplicated[identity] = _merge_cluster_values(current, cluster)
    return list(deduplicated.values())


def _cluster_identity_key(cluster: dict[str, Any]) -> tuple[str, ...]:
    url = _normalize_text(cluster.get("url")).lower()
    if url:
        return ("url", url)

    return (
        "content",
        _normalize_text(cluster.get("source")).lower(),
        _normalize_text(cluster.get("title")).lower(),
        _normalize_text(cluster.get("body")).lower(),
    )


def _sort_clusters(clusters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        clusters,
        key=lambda cluster: (
            _normalize_text(cluster.get("date")),
            _normalize_time(cluster.get("time")),
            _normalize_text(cluster.get("title")).lower(),
            _normalize_text(cluster.get("source")).lower(),
        ),
        reverse=True,
    )


def _apply_positions(clusters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    positioned_clusters: list[dict[str, Any]] = []
    for index, cluster in enumerate(clusters, start=1):
        positioned = dict(cluster)
        positioned["position"] = index
        positioned_clusters.append(positioned)
    return positioned_clusters


def _normalize_time(value: Any) -> str:
    time_value = _normalize_text(value)
    if not time_value:
        return ""

    return time_value.split(" ")[0]


def _merge_text_lists(*values: Any) -> list[str]:
    merged: list[str] = []
    for value in values:
        merged.extend(_normalize_text_list(value))

    return _normalize_text_list(merged)


def _normalize_text_list(value: Any) -> list[str]:
    if isinstance(value, str):
        normalized = value.strip()
        return [normalized] if normalized else []

    if isinstance(value, dict):
        if "name" in value:
            return _normalize_text_list(value.get("name"))
        if "term" in value:
            return _normalize_text_list(value.get("term"))
        if "value" in value:
            return _normalize_text_list(value.get("value"))
        return []

    if isinstance(value, (list, tuple, set)):
        candidates: list[str] = []
        for item in value:
            candidates.extend(_normalize_text_list(item))
    elif value is None:
        candidates = []
    else:
        candidates = [str(value).strip()]

    normalized_values: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        text = str(candidate or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized_values.append(text)

    return normalized_values


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _resolve_logo_path(output_filename: str) -> str:
    output_path = Path(output_filename)
    static_logo_path = Path(__file__).resolve().parent / "static" / "assets" / "logo.png"

    try:
        relative_path = os.path.relpath(static_logo_path, output_path.parent)
    except Exception:
        return static_logo_path.as_posix()

    return Path(relative_path).as_posix()
