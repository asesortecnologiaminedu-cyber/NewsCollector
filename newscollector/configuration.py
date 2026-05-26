from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

try:
    from .logging_utils import log_info
except ImportError:  # pragma: no cover - direct script execution support
    from logging_utils import log_info

PACKAGE_DIR = Path(__file__).resolve().parent


def _read_sources_json(file_path: Path) -> dict[str, Any]:
    with file_path.open(encoding="utf-8") as data:
        loaded_sources = json.load(data)

    if not isinstance(loaded_sources, dict):
        raise ValueError("Sources JSON must contain an object at its root.")

    return loaded_sources


def validate_date(value: date | str) -> tuple[date, date]:
    parsed_date = parse_date(value)
    return parsed_date, parsed_date - timedelta(days=1)


def parse_date(value: date | str) -> date:
    if isinstance(value, date):
        return value

    if not isinstance(value, str):
        raise TypeError("Parameter 'news_date' must be a date or YYYY-MM-DD string.")

    stripped_value = value.strip()
    if not stripped_value:
        raise ValueError("Parameter 'news_date' cannot be empty.")

    return datetime.strptime(stripped_value, "%Y-%m-%d").date()


def validate_template(template_name: str) -> tuple[str, str]:
    custom_template_path = Path("templates") / template_name
    if custom_template_path.exists():
        log_info(f'Using custom "{template_name}" as template file.')
        return template_name, "templates"

    package_template_name = "newsletter.html"
    package_template_dir = PACKAGE_DIR / "templates"
    log_info('Using package default "newsletter.html" as template file.')
    return package_template_name, str(package_template_dir)


def load_sources(file_name: str) -> dict[str, Any]:
    custom_source_path = Path(file_name)
    try:
        sources = _read_sources_json(custom_source_path)
        log_info(f'Using custom "{file_name}" as source file.')
        return sources
    except Exception:
        package_source_path = PACKAGE_DIR / "sources.json"
        try:
            sources = _read_sources_json(package_source_path)
            log_info('Using package default "sources.json" as source file.')
            return sources
        except Exception as exc:
            raise RuntimeError('Error in "load_sources()"') from exc


def validate_output_filename(file_name: str, news_date: date) -> str:
    if file_name == "default":
        output_dir = (
            PACKAGE_DIR
            / "rendered"
            / f"{news_date.year:04d}"
            / f"{news_date.month:02d}"
            / f"{news_date.day:02d}"
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        _migrate_legacy_default_outputs(news_date, output_dir)
        return str(output_dir / f"newsletter_{news_date}.html")

    output_path = Path(file_name)
    if output_path.parent != Path("."):
        output_path.parent.mkdir(parents=True, exist_ok=True)

    return str(output_path)


def validate_bool_parameter(value: bool, parameter_name: str) -> bool:
    if isinstance(value, bool):
        return value

    raise TypeError(f'Parameter "{parameter_name}" must be of type "bool".')


def _migrate_legacy_default_outputs(news_date: date, output_dir: Path) -> None:
    legacy_dir = PACKAGE_DIR / "rendered"
    base_name = f"newsletter_{news_date}"
    moved_files: list[str] = []

    for suffix in (".json", ".md", ".html"):
        legacy_path = legacy_dir / f"{base_name}{suffix}"
        destination_path = output_dir / f"{base_name}{suffix}"

        if not legacy_path.exists() or destination_path.exists():
            continue

        try:
            legacy_path.replace(destination_path)
            moved_files.append(destination_path.name)
        except Exception:
            continue

    if moved_files:
        log_info(
            "Migrated legacy rendered outputs into date folder: "
            + ", ".join(moved_files)
        )
