"""Sentiment scoring and sentiment-return correlation utilities."""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


POSITIVE_WORDS = {
    "beat",
    "beats",
    "bullish",
    "buy",
    "gain",
    "gains",
    "growth",
    "high",
    "higher",
    "outperform",
    "positive",
    "raise",
    "raised",
    "raises",
    "record",
    "strong",
    "surge",
    "upgrade",
    "upside",
}
NEGATIVE_WORDS = {
    "bearish",
    "cut",
    "decline",
    "downgrade",
    "drop",
    "falls",
    "loss",
    "low",
    "lower",
    "miss",
    "misses",
    "negative",
    "plunge",
    "risk",
    "sell",
    "slump",
    "weak",
    "warning",
}


@dataclass(frozen=True)
class SentimentToolInfo:
    name: str
    rationale: str


def sentiment_tool_info() -> SentimentToolInfo:
    """Return the selected sentiment tool rationale for reporting."""
    return SentimentToolInfo(
        name="VADER with lightweight fallback",
        rationale=(
            "VADER is selected because financial headlines are short, polarity-heavy text snippets. "
            "It performs well on concise social/news-like language and returns a normalized compound score. "
            "A small lexicon fallback keeps tests and basic runs reproducible when optional NLP packages are unavailable."
        ),
    )


def _vader_analyzer():
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

        return SentimentIntensityAnalyzer()
    except Exception:
        return None


def _fallback_sentiment(headline: str) -> float:
    tokens = {
        token.strip(".,;:!?()[]{}'\"").lower()
        for token in str(headline).split()
        if token.strip()
    }
    positive = len(tokens.intersection(POSITIVE_WORDS))
    negative = len(tokens.intersection(NEGATIVE_WORDS))
    total = positive + negative
    if total == 0:
        return 0.0
    return (positive - negative) / total


def score_headlines(news: pd.DataFrame, headline_column: str = "headline") -> pd.DataFrame:
    """Add numerical sentiment scores and sentiment labels to news headlines."""
    scored = news.copy()
    analyzer = _vader_analyzer()
    if analyzer is not None:
        scored["sentiment_score"] = scored[headline_column].fillna("").map(
            lambda text: analyzer.polarity_scores(str(text))["compound"]
        )
        scored["sentiment_tool"] = "vader"
    else:
        scored["sentiment_score"] = scored[headline_column].fillna("").map(_fallback_sentiment)
        scored["sentiment_tool"] = "fallback_lexicon"

    scored["sentiment_label"] = classify_sentiment(scored["sentiment_score"])
    return scored


def classify_sentiment(scores: pd.Series, threshold: float = 0.05) -> pd.Series:
    """Classify sentiment scores as positive, neutral, or negative."""
    return pd.Series(
        np.select(
            [scores > threshold, scores < -threshold],
            ["positive", "negative"],
            default="neutral",
        ),
        index=scores.index,
        name="sentiment_label",
    )


def _next_trading_day(date: pd.Timestamp, trading_dates: list[pd.Timestamp]) -> pd.Timestamp | pd.NaT:
    position = bisect_left(trading_dates, date.normalize())
    if position >= len(trading_dates):
        return pd.NaT
    return trading_dates[position]


def align_news_to_trading_day(
    news: pd.DataFrame,
    prices: pd.DataFrame,
    date_column: str = "date",
    stock_column: str = "stock",
) -> pd.DataFrame:
    """Align each news item to the same or next available trading day for its stock."""
    aligned = news.copy()
    aligned[date_column] = pd.to_datetime(aligned[date_column], errors="coerce", utc=True)
    aligned["publication_date"] = aligned[date_column].dt.tz_convert(None).dt.normalize()

    price_frame = prices.copy()
    price_frame["date"] = pd.to_datetime(price_frame["date"], errors="coerce").dt.normalize()
    if stock_column in price_frame.columns:
        price_frame[stock_column] = price_frame[stock_column].astype(str).str.upper().str.strip()
        trading_calendar = {
            stock: sorted(group["date"].dropna().unique())
            for stock, group in price_frame.groupby(stock_column)
        }
    else:
        trading_calendar = {"__all__": sorted(price_frame["date"].dropna().unique())}

    def map_row(row: pd.Series) -> pd.Timestamp | pd.NaT:
        stock = str(row.get(stock_column, "__all__")).upper().strip()
        calendar = trading_calendar.get(stock) or trading_calendar.get("__all__", [])
        if not calendar or pd.isna(row["publication_date"]):
            return pd.NaT
        calendar_timestamps = [pd.Timestamp(day) for day in calendar]
        return _next_trading_day(row["publication_date"], calendar_timestamps)

    aligned["trading_date"] = aligned.apply(map_row, axis=1)
    return aligned.dropna(subset=["trading_date"])


def aggregate_daily_sentiment(
    aligned_news: pd.DataFrame,
    stock_column: str = "stock",
) -> pd.DataFrame:
    """Average sentiment when multiple articles exist for the same stock/day."""
    group_columns = [stock_column, "trading_date"] if stock_column in aligned_news.columns else ["trading_date"]
    grouped = (
        aligned_news.groupby(group_columns)
        .agg(
            avg_sentiment=("sentiment_score", "mean"),
            article_count=("sentiment_score", "size"),
        )
        .reset_index()
    )
    grouped["sentiment_label"] = classify_sentiment(grouped["avg_sentiment"])
    return grouped


def compute_daily_returns(
    prices: pd.DataFrame,
    price_column: str = "adj_close",
    stock_column: str = "stock",
) -> pd.DataFrame:
    """Compute daily percentage returns from adjusted close prices."""
    returns = prices.copy()
    returns["date"] = pd.to_datetime(returns["date"], errors="coerce").dt.normalize()
    if price_column not in returns.columns:
        price_column = "close"
    returns = returns.sort_values([stock_column, "date"] if stock_column in returns.columns else ["date"])

    if stock_column in returns.columns:
        returns["daily_return_pct"] = returns.groupby(stock_column)[price_column].pct_change() * 100
    else:
        returns["daily_return_pct"] = returns[price_column].pct_change() * 100

    selected_columns = [column for column in [stock_column, "date", price_column, "daily_return_pct"] if column in returns.columns]
    return returns[selected_columns].dropna(subset=["daily_return_pct"])


def merge_sentiment_with_returns(
    daily_sentiment: pd.DataFrame,
    daily_returns: pd.DataFrame,
    stock_column: str = "stock",
) -> pd.DataFrame:
    """Join average daily sentiment to daily stock returns."""
    left = daily_sentiment.rename(columns={"trading_date": "date"}).copy()
    right = daily_returns.copy()
    merge_columns = [stock_column, "date"] if stock_column in left.columns and stock_column in right.columns else ["date"]
    merged = left.merge(right, on=merge_columns, how="inner")
    return merged.dropna(subset=["avg_sentiment", "daily_return_pct"])


def pearson_correlation(
    merged: pd.DataFrame,
    stock_column: str = "stock",
) -> pd.DataFrame:
    """Calculate Pearson correlation between daily sentiment and returns."""
    if merged.empty:
        return pd.DataFrame(columns=[stock_column, "observations", "pearson_correlation"])

    rows = []
    groups: Iterable[tuple[str, pd.DataFrame]]
    if stock_column in merged.columns:
        groups = merged.groupby(stock_column)
    else:
        groups = [("all", merged)]

    for stock, group in groups:
        valid = group[["avg_sentiment", "daily_return_pct"]].dropna()
        correlation = (
            valid["avg_sentiment"].corr(valid["daily_return_pct"], method="pearson")
            if len(valid) >= 2
            else np.nan
        )
        rows.append(
            {
                stock_column: stock,
                "observations": len(valid),
                "pearson_correlation": correlation,
            }
        )
    return pd.DataFrame(rows).sort_values("observations", ascending=False)


def average_return_by_sentiment(merged: pd.DataFrame) -> pd.DataFrame:
    """Summarize average daily return by sentiment category."""
    return (
        merged.groupby("sentiment_label")
        .agg(
            avg_daily_return_pct=("daily_return_pct", "mean"),
            observations=("daily_return_pct", "size"),
        )
        .reindex(["negative", "neutral", "positive"])
        .dropna(how="all")
        .reset_index()
    )
