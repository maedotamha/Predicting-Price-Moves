"""Reusable EDA helpers for financial news headlines."""

from __future__ import annotations

import re

import pandas as pd
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer


def headline_length_summary(news: pd.DataFrame) -> pd.DataFrame:
    """Return descriptive statistics for headline character and word counts."""
    return news[["headline_char_count", "headline_word_count"]].describe().T


def top_counts(news: pd.DataFrame, column: str, n: int = 15) -> pd.Series:
    """Return the top n value counts for a news column."""
    return news[column].value_counts().head(n)


def daily_article_volume(news: pd.DataFrame) -> pd.DataFrame:
    """Count articles published per calendar day."""
    daily = news.groupby("publication_date").size().rename("article_count")
    return daily.reset_index()


def hourly_article_volume(news: pd.DataFrame) -> pd.DataFrame:
    """Count articles by UTC publication hour."""
    hourly = news.groupby("publication_hour").size().rename("article_count")
    return hourly.reset_index()


def extract_publisher_domain(publisher: str) -> str:
    """Extract an email domain from publisher values when present."""
    match = re.search(r"@([A-Za-z0-9.-]+\.[A-Za-z]{2,})", str(publisher))
    return match.group(1).lower() if match else "not_email"


def publisher_domain_counts(news: pd.DataFrame, n: int = 15) -> pd.Series:
    """Count publisher email domains when publisher names are email addresses."""
    domains = news["publisher"].map(extract_publisher_domain)
    return domains.value_counts().head(n)


def top_tfidf_terms(
    headlines: pd.Series,
    n: int = 20,
    ngram_range: tuple[int, int] = (1, 2),
) -> pd.DataFrame:
    """Extract high-signal words and phrases from headlines with TF-IDF."""
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=ngram_range,
        min_df=2,
        max_df=0.9,
    )
    matrix = vectorizer.fit_transform(headlines.fillna(""))
    scores = matrix.mean(axis=0).A1
    terms = vectorizer.get_feature_names_out()
    result = pd.DataFrame({"term": terms, "score": scores})
    return result.sort_values("score", ascending=False).head(n).reset_index(drop=True)


def lda_topics(
    headlines: pd.Series,
    n_topics: int = 5,
    n_terms: int = 8,
    random_state: int = 42,
) -> pd.DataFrame:
    """Fit a compact LDA topic model and return top terms per topic."""
    vectorizer = CountVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.9,
    )
    matrix = vectorizer.fit_transform(headlines.fillna(""))
    model = LatentDirichletAllocation(
        n_components=n_topics,
        random_state=random_state,
        learning_method="batch",
    )
    model.fit(matrix)

    terms = vectorizer.get_feature_names_out()
    rows = []
    for topic_index, topic_weights in enumerate(model.components_, start=1):
        top_indices = topic_weights.argsort()[-n_terms:][::-1]
        rows.append(
            {
                "topic": f"Topic {topic_index}",
                "top_terms": ", ".join(terms[index] for index in top_indices),
            }
        )
    return pd.DataFrame(rows)
