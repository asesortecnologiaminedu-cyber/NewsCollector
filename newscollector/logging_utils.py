from __future__ import annotations

from datetime import datetime

import pandas as pd


def log_info(message: str) -> None:
    print(f"INFO: {message}")


def log_warn(message: str) -> None:
    print(f"WARN: {message}")


def print_scrape_status(count: int) -> None:
    print(f"Scraped {count} articles", end="\r")


def print_scrape_result(df: pd.DataFrame, start: datetime, end: datetime) -> None:
    elapsed_seconds = int((end - start).total_seconds())
    minutes, seconds = divmod(elapsed_seconds, 60)

    if df.empty or "source" not in df.columns:
        print(f"0 total articles downloaded in {minutes} min {seconds} sec\n")
        return

    for source in sorted(set(df["source"])):
        source_count = int((df["source"] == source).sum())
        print(f"{source_count} articles downloaded from {source}\n", end="\r")

    print(f"{len(df['source'])} total articles downloaded in {minutes} min {seconds} sec\n")
