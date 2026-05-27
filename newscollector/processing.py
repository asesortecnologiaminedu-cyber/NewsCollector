from __future__ import annotations

import random
import string
from typing import Any

import numpy as np
import pandas as pd
from gensim.parsing.preprocessing import remove_stopwords
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import word_tokenize
from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer
from unidecode import unidecode

try:
    from .logging_utils import log_info, log_warn
except ImportError:  # pragma: no cover - direct script execution support
    from logging_utils import log_info, log_warn

Cluster = list[pd.Series]
Clusters = dict[int, Cluster]

_PUNCTUATION_TRANSLATOR = str.maketrans("", "", string.punctuation)
_DIGIT_TRANSLATOR = str.maketrans("", "", string.digits)


def write_dataframe(articles: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.json_normalize(articles)


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    required_columns = ["title", "body", "image_url"]
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        log_warn(f"Cannot clean dataframe, missing columns: {missing_columns}")
        return df.iloc[0:0].copy()

    working_df = df.copy()
    start_count = len(working_df)

    working_df["title"] = working_df["title"].fillna("")
    working_df["body"] = working_df["body"].fillna("")
    working_df["image_url"] = working_df["image_url"].fillna("")

    working_df = working_df[working_df.title != ""]
    working_df = working_df[working_df.body != ""]
    working_df = working_df[working_df.image_url != ""]
    after_presence = len(working_df)

    working_df = working_df[working_df.title.str.count(r"\s+").ge(3)]
    working_df = working_df[working_df.body.str.count(r"\s+").ge(20)]
    after_length = len(working_df)

    log_info(
        "Clean dataframe rows: "
        f"start={start_count}, after_presence={after_presence}, after_length={after_length}"
    )

    return working_df


def clean_articles(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        log_warn("No rows to clean in clean_articles().")
        empty_df = df.copy()
        empty_df["clean_body"] = ""
        return empty_df

    working_df = df.copy()
    start_count = len(working_df)

    working_df = working_df.drop_duplicates(subset=["title", "source"]).sort_index()
    working_df = working_df.drop_duplicates(subset=["body"]).sort_index()
    working_df = working_df.drop_duplicates(subset=["url"]).sort_index()
    working_df = working_df.reset_index(drop=True)
    after_dedup = len(working_df)

    clean_body = working_df["body"].astype(str).str.lower()
    clean_body = clean_body.map(remove_stopwords)
    clean_body = clean_body.str.translate(_PUNCTUATION_TRANSLATOR)
    clean_body = clean_body.str.translate(_DIGIT_TRANSLATOR)

    for source_name in {source.lower() for source in working_df["source"].astype(str)}:
        clean_body = clean_body.str.replace(source_name, "", regex=False)

    clean_body = clean_body.map(unidecode)
    tokenized_body = clean_body.map(word_tokenize)

    stemmer = SnowballStemmer(language="english")
    stemmed_body = tokenized_body.map(lambda words: [stemmer.stem(word) for word in words])
    working_df["clean_body"] = stemmed_body.map(" ".join)

    non_empty_clean = int(working_df["clean_body"].fillna("").astype(str).str.strip().ne("").sum())
    log_info(
        "Clean articles rows: "
        f"start={start_count}, after_dedup={after_dedup}, non_empty_clean_body={non_empty_clean}"
    )

    return working_df


def compute_tfidf(df: pd.DataFrame) -> tuple[np.ndarray, pd.DataFrame]:
    clean_body = df["clean_body"].fillna("").astype(str).str.strip()
    valid_rows = clean_body.ne("")
    log_info(f"TF-IDF input rows: total={len(df)}, non_empty={int(valid_rows.sum())}")

    if not valid_rows.any():
        log_warn("No non-empty clean_body rows found after preprocessing.")
        return np.empty((0, 0)), df.iloc[0:0].copy()

    filtered_df = df.loc[valid_rows].reset_index(drop=True)

    try:
        tfidf_matrix = TfidfVectorizer().fit_transform(filtered_df["clean_body"]).toarray()
    except ValueError as exc:
        if "empty vocabulary" in str(exc).lower():
            log_warn("TF-IDF produced empty vocabulary after preprocessing.")
            return np.empty((0, 0)), df.iloc[0:0].copy()
        raise

    log_info(f"TF-IDF matrix shape: {tfidf_matrix.shape[0]} rows x {tfidf_matrix.shape[1]} terms")
    return tfidf_matrix, filtered_df


def find_clusters(
    df: pd.DataFrame,
    tfidf_matrix: np.ndarray,
    distance_threshold: float = 1,
) -> Clusters:
    if len(df) < 2 or len(tfidf_matrix) < 2:
        log_warn("Skipping clustering because fewer than 2 valid articles are available.")
        return {}

    agglomerative = AgglomerativeClustering(
        distance_threshold=distance_threshold,
        n_clusters=None,
    )
    labels = agglomerative.fit_predict(tfidf_matrix)

    label_counts = pd.Series(labels).value_counts().sort_values(ascending=False)
    clusters: Clusters = {}

    featured_cluster_index = 0
    for cluster_label, cluster_size in label_counts.items():
        if int(cluster_size) < 2:
            break

        row_indexes = np.argwhere(labels == cluster_label).flatten("C").tolist()
        clusters[featured_cluster_index] = [df.iloc[index] for index in row_indexes]
        featured_cluster_index += 1

    log_info(
        f"Clustering complete: {len(set(labels))} labels, {len(clusters)} featured clusters"
    )
    return clusters


def find_featured_clusters(clusters: Clusters) -> Clusters:
    return clusters


def shuffle_content(clusters: Clusters) -> None:
    for cluster_index in list(clusters):
        try:
            random.shuffle(clusters[cluster_index])
        except Exception:
            continue


def prettify_similar(clusters: Clusters) -> dict[int, dict[str, list[str]]]:
    similar_articles: dict[int, dict[str, list[str]]] = {}

    for cluster_index in list(clusters):
        similar_articles[cluster_index] = {}
        cluster_articles = clusters[cluster_index]

        if len(cluster_articles) >= 4:
            similar_articles[cluster_index]["source"] = [
                f"{cluster_articles[1]['source']} ",
                f"| {cluster_articles[2]['source']} ",
                f"| {cluster_articles[3]['source']}",
            ]
            similar_articles[cluster_index]["url"] = [
                cluster_articles[1]["url"],
                cluster_articles[2]["url"],
                cluster_articles[3]["url"],
            ]
            continue

        if len(cluster_articles) == 3:
            similar_articles[cluster_index]["source"] = [
                f"{cluster_articles[1]['source']} ",
                f"| {cluster_articles[2]['source']}",
                "",
            ]
            similar_articles[cluster_index]["url"] = [
                cluster_articles[1]["url"],
                cluster_articles[2]["url"],
                "",
            ]
            continue

        if len(cluster_articles) == 2:
            similar_articles[cluster_index]["source"] = [cluster_articles[1]["source"], "", ""]
            similar_articles[cluster_index]["url"] = [cluster_articles[1]["url"], "", ""]
            continue

        similar_articles[cluster_index]["source"] = ["None", "", ""]
        similar_articles[cluster_index]["url"] = ["", "", ""]

    return similar_articles
