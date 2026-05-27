from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from newscollector.rendering import _resolve_logo_path, build_html


class RenderingTests(unittest.TestCase):
    def test_resolve_logo_path_for_default_partition_output(self) -> None:
        logo_path = _resolve_logo_path(
            "/home/nicolai/workspaces/NewsCollector/newscollector/rendered/2026/05/26/newsletter_2026-05-26.html"
        )
        self.assertEqual(logo_path, "../../../../static/assets/logo.png")

    def test_build_html_writes_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            template_name = "simple_template.html"
            output_file = temp_path / "newsletter.html"
            markdown_file = temp_path / "newsletter.md"
            json_file = temp_path / "newsletter.json"

            (temp_path / template_name).write_text(
                "<h1>{{news_name}}</h1>{% for cluster in clusters %}<p>{{cluster.title}}</p>{% endfor %}",
                encoding="utf-8",
            )

            clusters = {
                0: [
                    {
                        "source": "Source A",
                        "url": "https://example.com/1",
                        "image_url": "https://example.com/image.png",
                        "title": "Headline",
                        "body": "Body text",
                        "authors": ["Author One", "Author Two"],
                        "actor": ["Actor A"],
                    },
                    {
                        "source": "Source B",
                        "url": "https://example.com/2",
                        "image_url": "https://example.com/image2.png",
                        "title": "Related",
                        "body": "Related body",
                        "authors": ["Author One", "Author Two"],
                        "actor": ["Actor A"],
                    },
                ]
            }

            was_written = build_html(
                clusters_dict=clusters,
                news_name="My News",
                news_date="2026-05-26",
                template=template_name,
                output_filename=str(output_file),
                template_path=str(temp_path),
            )

            self.assertTrue(was_written)
            self.assertTrue(output_file.exists())
            self.assertTrue(markdown_file.exists())
            self.assertTrue(json_file.exists())

            rendered = output_file.read_text(encoding="utf-8")
            markdown_rendered = markdown_file.read_text(encoding="utf-8")
            consolidated_report = json.loads(json_file.read_text(encoding="utf-8"))

            self.assertIn("My News", rendered)
            self.assertEqual(consolidated_report["news_name"], "My News")
            self.assertEqual(consolidated_report["schema_version"], "1.1")

            consolidated_title = consolidated_report["clusters"][0]["title"]
            self.assertIn(consolidated_title, rendered)
            self.assertIn(consolidated_title, markdown_rendered)

            first_cluster = consolidated_report["clusters"][0]
            self.assertEqual(first_cluster["authors"], ["Author One", "Author Two"])
            self.assertEqual(first_cluster["actor"], ["Actor A"])

    def test_build_html_merges_existing_daily_json_without_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            template_name = "simple_template.html"
            output_file = temp_path / "newsletter_2026-05-26.html"
            json_file = temp_path / "newsletter_2026-05-26.json"

            (temp_path / template_name).write_text(
                "<h1>{{news_name}}</h1>{% for cluster in clusters %}<article>{{cluster.title}}</article>{% endfor %}",
                encoding="utf-8",
            )

            existing_report = {
                "schema_version": "1.1",
                "news_name": "My News",
                "news_date": "2026-05-26",
                "clusters": [
                    {
                        "position": 1,
                        "date": "2026-05-26",
                        "time": "08:00:00",
                        "source": "Source A",
                        "url": "https://example.com/1",
                        "pic": "https://example.com/image.png",
                        "title": "Existing headline",
                        "body": "Existing body",
                        "authors": ["Author Existing"],
                        "actor": ["Actor Existing"],
                        "similar": [],
                    }
                ],
            }
            json_file.write_text(json.dumps(existing_report), encoding="utf-8")

            clusters = {
                0: [
                    {
                        "source": "Source A",
                        "url": "https://example.com/1",
                        "image_url": "https://example.com/image.png",
                        "title": "Existing headline updated",
                        "body": "Existing body updated",
                        "date": "2026-05-26",
                        "time": "09:00:00 UTC",
                        "authors": ["Author Incoming"],
                        "actor": ["Actor Existing", "Actor Incoming"],
                    }
                ],
                1: [
                    {
                        "source": "Source B",
                        "url": "https://example.com/2",
                        "image_url": "https://example.com/image2.png",
                        "title": "New headline",
                        "body": "New body",
                        "date": "2026-05-26",
                        "time": "10:00:00 UTC",
                    }
                ],
            }

            was_written = build_html(
                clusters_dict=clusters,
                news_name="My News",
                news_date="2026-05-26",
                template=template_name,
                output_filename=str(output_file),
                template_path=str(temp_path),
            )

            self.assertTrue(was_written)
            merged_report = json.loads(json_file.read_text(encoding="utf-8"))
            merged_clusters = merged_report["clusters"]

            self.assertEqual(len(merged_clusters), 2)
            self.assertEqual(merged_clusters[0]["url"], "https://example.com/2")
            self.assertEqual(merged_clusters[1]["url"], "https://example.com/1")
            self.assertEqual(merged_clusters[1]["title"], "Existing headline updated")
            self.assertEqual(merged_clusters[1]["authors"], ["Author Existing", "Author Incoming"])
            self.assertEqual(
                merged_clusters[1]["actor"],
                ["Actor Existing", "Actor Incoming"],
            )


if __name__ == "__main__":
    unittest.main()
