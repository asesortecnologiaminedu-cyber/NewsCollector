from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from newscollector.configuration import (
    load_sources,
    parse_date,
    validate_bool_parameter,
    validate_output_filename,
    validate_template,
)


class ConfigurationTests(unittest.TestCase):
    def test_parse_date_from_string(self) -> None:
        parsed = parse_date("2026-05-26")
        self.assertEqual(parsed, date(2026, 5, 26))

    def test_parse_date_invalid_type_raises(self) -> None:
        with self.assertRaises(TypeError):
            parse_date(123)  # type: ignore[arg-type]

    def test_validate_bool_parameter_returns_bool(self) -> None:
        self.assertTrue(validate_bool_parameter(True, "auto_open"))
        self.assertFalse(validate_bool_parameter(False, "return_details"))

        with self.assertRaises(TypeError):
            validate_bool_parameter("yes", "auto_open")  # type: ignore[arg-type]

    def test_validate_template_falls_back_to_package_default(self) -> None:
        template_name, template_path = validate_template("missing-template.html")
        self.assertEqual(template_name, "newsletter.html")
        self.assertTrue(Path(template_path).exists())

    def test_load_sources_reads_custom_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "sources.json"
            temp_path.write_text(
                json.dumps({"Example": {"rss": ["https://example.com/feed"]}}),
                encoding="utf-8",
            )

            loaded_sources = load_sources(str(temp_path))
            self.assertIn("Example", loaded_sources)

    def test_validate_output_filename_default_is_date_partitioned(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package_dir = Path(temp_dir)
            with patch("newscollector.configuration.PACKAGE_DIR", package_dir):
                output_path = Path(validate_output_filename("default", date(2026, 5, 26)))

            self.assertEqual(output_path.name, "newsletter_2026-05-26.html")
            self.assertEqual(output_path.parent.name, "26")
            self.assertEqual(output_path.parent.parent.name, "05")
            self.assertEqual(output_path.parent.parent.parent.name, "2026")

    def test_validate_output_filename_migrates_legacy_flat_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package_dir = Path(temp_dir)
            legacy_rendered_dir = package_dir / "rendered"
            legacy_rendered_dir.mkdir(parents=True, exist_ok=True)

            (legacy_rendered_dir / "newsletter_2026-05-26.html").write_text(
                "legacy html",
                encoding="utf-8",
            )
            (legacy_rendered_dir / "newsletter_2026-05-26.md").write_text(
                "legacy md",
                encoding="utf-8",
            )
            (legacy_rendered_dir / "newsletter_2026-05-26.json").write_text(
                "{}",
                encoding="utf-8",
            )

            with patch("newscollector.configuration.PACKAGE_DIR", package_dir):
                output_path = Path(validate_output_filename("default", date(2026, 5, 26)))

            self.assertTrue(output_path.exists())
            self.assertTrue((output_path.with_suffix(".md")).exists())
            self.assertTrue((output_path.with_suffix(".json")).exists())
            self.assertFalse((legacy_rendered_dir / "newsletter_2026-05-26.html").exists())


if __name__ == "__main__":
    unittest.main()
