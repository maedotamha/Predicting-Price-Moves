"""Data loading utilities for FNSPID-style financial news files."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_NEWS_COLUMNS = {"headline", "url", "publisher", "date", "stock"}
DEFAULT_NEWS_FILENAMES = (
    "financial_news.csv",
    "fspnid.csv",
    "fns_full_news.csv",
    "news.csv",
    "raw_analyst_ratings.csv",
)


def find_news_file(raw_dir: str | Path = "data/raw") -> Path:
    """Return the first likely FNSPID CSV file in the raw data directory."""
    raw_path = Path(raw_dir)
    for filename in DEFAULT_NEWS_FILENAMES:
        candidate = raw_path / filename
        if candidate.exists():
            return candidate

    csv_files = sorted(raw_path.glob("*.csv"))
    if csv_files:
        return csv_files[0]

    raise FileNotFoundError(
        f"No CSV file found in {raw_path}. Add the FNSPID news CSV to data/raw/."
    )


def load_news(path: str | Path | None = None) -> pd.DataFrame:
    """Load and lightly standardize a financial news CSV."""
    if path is None:
        news_path = find_news_file()
    else:
        candidate = Path(path)
        news_path = find_news_file(candidate) if candidate.is_dir() else candidate

    news = pd.read_csv(news_path)
    news.columns = [column.strip().lower().replace(" ", "_") for column in news.columns]

    missing = REQUIRED_NEWS_COLUMNS.difference(news.columns)
    if missing:
        missing_columns = ", ".join(sorted(missing))
        raise ValueError(f"News file is missing required columns: {missing_columns}")

    news = news.copy()
    news["headline"] = news["headline"].fillna("").astype(str).str.strip()
    news["publisher"] = news["publisher"].fillna("unknown").astype(str).str.strip()
    news["stock"] = news["stock"].fillna("unknown").astype(str).str.upper().str.strip()
    news["date"] = pd.to_datetime(news["date"], errors="coerce", utc=True)
    news = news.dropna(subset=["date"])
    news["publication_date"] = news["date"].dt.date
    news["publication_hour"] = news["date"].dt.hour
    news["headline_char_count"] = news["headline"].str.len()
    news["headline_word_count"] = news["headline"].str.split().str.len()
    return news
