from __future__ import annotations

import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from newscollector.processing import (
    clean_articles,
    clean_dataframe,
    compute_tfidf,
    find_clusters,
)


class ProcessingTests(unittest.TestCase):
    def test_clean_dataframe_filters_invalid_rows(self) -> None:
        dataframe = pd.DataFrame(
            {
                "title": [
                    "A valid title with enough words",
                    "too short",
                ],
                "body": [
                    "This is a valid body with enough words to pass the minimum threshold for filtering and processing with additional text to exceed the whitespace requirement safely.",
                    "small body",
                ],
                "image_url": ["https://img/1.png", ""],
            }
        )

        cleaned = clean_dataframe(dataframe)
        self.assertEqual(len(cleaned), 1)

    def test_clean_articles_creates_clean_body_and_deduplicates(self) -> None:
        dataframe = pd.DataFrame(
            {
                "title": ["Title one long enough", "Title one long enough", "Another title long enough"],
                "source": ["Alpha", "Alpha", "Beta"],
                "body": [
                    "Alpha writes an article about economy and politics with repeated words.",
                    "Alpha writes an article about economy and politics with repeated words.",
                    "Beta reports another story with content and extra words included.",
                ],
                "url": ["https://example.com/1", "https://example.com/1", "https://example.com/2"],
                "image_url": ["https://img/1.png", "https://img/1.png", "https://img/2.png"],
            }
        )

        with patch("newscollector.processing.word_tokenize", side_effect=lambda value: value.split()):
            cleaned = clean_articles(dataframe)

        self.assertIn("clean_body", cleaned.columns)
        self.assertEqual(len(cleaned), 2)
        self.assertTrue(cleaned["clean_body"].str.len().gt(0).all())

    def test_compute_tfidf_returns_empty_when_no_content(self) -> None:
        dataframe = pd.DataFrame({"clean_body": ["", "   "]})
        matrix, filtered = compute_tfidf(dataframe)
        self.assertEqual(matrix.shape, (0, 0))
        self.assertTrue(filtered.empty)

    def test_find_clusters_returns_featured_cluster(self) -> None:
        dataframe = pd.DataFrame({"clean_body": ["apple banana", "apple banana", "zebra yak"]})
        matrix, filtered = compute_tfidf(dataframe)

        clusters = find_clusters(filtered, matrix, distance_threshold=0.1)
        self.assertTrue(clusters)
        self.assertEqual(len(clusters[0]), 2)
        self.assertIsInstance(matrix, np.ndarray)


if __name__ == "__main__":
    unittest.main()
