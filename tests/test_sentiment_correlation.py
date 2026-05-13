import pandas as pd

from src.sentiment_correlation import (
    aggregate_daily_sentiment,
    align_news_to_trading_day,
    average_return_by_sentiment,
    compute_daily_returns,
    merge_sentiment_with_returns,
    pearson_correlation,
    score_headlines,
)


def sample_prices() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-05", "2024-01-08", "2024-01-09"]),
            "stock": ["AAPL", "AAPL", "AAPL"],
            "adj_close": [100.0, 104.0, 102.0],
            "close": [100.0, 104.0, 102.0],
        }
    )


def sample_news() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "headline": [
                "Apple beats earnings estimates",
                "Apple shares fall after warning",
            ],
            "date": pd.to_datetime(
                ["2024-01-06 10:00:00-04:00", "2024-01-09 09:30:00-04:00"],
                utc=True,
            ),
            "stock": ["AAPL", "AAPL"],
        }
    )


def test_score_headlines_adds_score_and_label():
    scored = score_headlines(sample_news())

    assert "sentiment_score" in scored.columns
    assert set(scored["sentiment_label"]).issubset({"positive", "neutral", "negative"})


def test_weekend_news_aligns_to_next_trading_day():
    aligned = align_news_to_trading_day(sample_news(), sample_prices())

    assert aligned.loc[0, "trading_date"] == pd.Timestamp("2024-01-08")


def test_sentiment_return_merge_and_correlation():
    scored = score_headlines(sample_news())
    aligned = align_news_to_trading_day(scored, sample_prices())
    daily_sentiment = aggregate_daily_sentiment(aligned)
    daily_returns = compute_daily_returns(sample_prices())
    merged = merge_sentiment_with_returns(daily_sentiment, daily_returns)
    correlations = pearson_correlation(merged)
    by_label = average_return_by_sentiment(merged)

    assert len(merged) == 2
    assert correlations.loc[0, "observations"] == 2
    assert {"sentiment_label", "avg_daily_return_pct"}.issubset(by_label.columns)
