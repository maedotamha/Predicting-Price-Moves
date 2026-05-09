import pandas as pd

from src.eda import (
    daily_article_volume,
    extract_publisher_domain,
    headline_length_summary,
    hourly_article_volume,
    top_counts,
)


def sample_news() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "headline": [
                "Apple beats earnings estimates",
                "Tesla shares fall after delivery miss",
                "Apple gets price target upgrade",
            ],
            "publisher": ["analyst@example.com", "Reuters", "editor@news.co"],
            "stock": ["AAPL", "TSLA", "AAPL"],
            "date": pd.to_datetime(
                [
                    "2024-01-02 13:30:00+00:00",
                    "2024-01-02 15:00:00+00:00",
                    "2024-01-03 09:00:00+00:00",
                ],
                utc=True,
            ),
        }
    ).assign(
        publication_date=lambda frame: frame["date"].dt.date,
        publication_hour=lambda frame: frame["date"].dt.hour,
        headline_char_count=lambda frame: frame["headline"].str.len(),
        headline_word_count=lambda frame: frame["headline"].str.split().str.len(),
    )


def test_headline_length_summary_has_expected_metrics():
    summary = headline_length_summary(sample_news())

    assert "headline_char_count" in summary.index
    assert "mean" in summary.columns


def test_top_counts_returns_most_common_values():
    counts = top_counts(sample_news(), "stock", n=1)

    assert counts.index[0] == "AAPL"
    assert counts.iloc[0] == 2


def test_daily_and_hourly_volume_counts_articles():
    news = sample_news()

    assert daily_article_volume(news)["article_count"].tolist() == [2, 1]
    assert hourly_article_volume(news)["article_count"].sum() == 3


def test_extract_publisher_domain_only_for_email_values():
    assert extract_publisher_domain("analyst@example.com") == "example.com"
    assert extract_publisher_domain("Reuters") == "not_email"
