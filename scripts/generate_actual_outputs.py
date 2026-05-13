from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import requests
import seaborn as sns
import yfinance as yf

from src.data_loader import load_news
from src.eda import daily_article_volume, headline_length_summary, hourly_article_volume, top_counts, top_tfidf_terms
from src.sentiment_correlation import (
    aggregate_daily_sentiment,
    align_news_to_trading_day,
    average_return_by_sentiment,
    compute_daily_returns,
    merge_sentiment_with_returns,
    pearson_correlation,
    score_headlines,
)
from src.technical_indicators import add_indicators_by_stock, clean_price_data, compute_pynance_metrics, load_price_data


RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
SUMMARY_PATH = PROJECT_ROOT / "reports" / "actual_analysis_summary.json"
NEWS_URL = "https://huggingface.co/datasets/Zihan1004/FNSPID/resolve/main/Stock_news/nasdaq_exteral_data.csv"


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def download_news_sample(max_rows: int = 2500) -> Path:
    """Stream a manageable FNSPID sample and normalize it to the project schema."""
    output = RAW_DIR / "financial_news.csv"
    if output.exists() and output.stat().st_size > 100:
        return output

    response = requests.get(NEWS_URL, stream=True, timeout=90)
    response.raise_for_status()
    text_stream = io.TextIOWrapper(response.raw, encoding="utf-8", newline="")
    reader = csv.DictReader(text_stream)

    rows = []
    for row in reader:
        headline = (row.get("Article_title") or "").strip()
        stock = (row.get("Stock_symbol") or "").strip().upper()
        date = (row.get("Date") or "").strip()
        if not headline or not stock or not date:
            continue
        rows.append(
            {
                "headline": headline,
                "url": row.get("Url") or "",
                "publisher": row.get("Publisher") or row.get("Author") or "Nasdaq",
                "date": date,
                "stock": stock,
            }
        )
        if len(rows) >= max_rows:
            break

    pd.DataFrame(rows).to_csv(output, index=False)
    return output


def download_prices(tickers: list[str], start: str, end: str) -> Path:
    output = RAW_DIR / "stock_prices.csv"
    frames = []
    for ticker in tickers:
        data = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False)
        if data.empty:
            continue
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        data = data.reset_index()
        data["Stock"] = ticker
        frames.append(data)

    if not frames:
        raise RuntimeError("No stock price data could be downloaded from yfinance.")

    prices = pd.concat(frames, ignore_index=True)
    prices.to_csv(output, index=False)
    return output


def save_top_publishers(top_publishers: pd.Series) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    top_publishers.sort_values().plot(kind="barh", ax=ax, color="#4C78A8")
    ax.set_title("Top Publishers by Article Count")
    ax.set_xlabel("Articles")
    ax.set_ylabel("Publisher")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "actual_top_publishers.png", dpi=160)
    plt.close(fig)


def save_daily_volume(daily_volume: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.lineplot(data=daily_volume, x="publication_date", y="article_count", ax=ax, color="#54A24B")
    ax.set_title("Daily Financial News Volume")
    ax.set_xlabel("Publication date")
    ax.set_ylabel("Articles")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "actual_daily_news_volume.png", dpi=160)
    plt.close(fig)


def save_terms(terms: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 7))
    sns.barplot(data=terms.head(15), y="term", x="score", ax=ax, color="#F58518")
    ax.set_title("Top TF-IDF Headline Terms and Phrases")
    ax.set_xlabel("Mean TF-IDF score")
    ax.set_ylabel("Term")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "actual_top_tfidf_terms.png", dpi=160)
    plt.close(fig)


def save_technical_plots(plot_data: pd.DataFrame, ticker: str) -> None:
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(plot_data["date"], plot_data["adj_close"], label="Adj Close", color="#2F4B7C", linewidth=1.8)
    for column, color in [("sma_20", "#F58518"), ("sma_50", "#54A24B"), ("ema_20", "#B279A2")]:
        ax.plot(plot_data["date"], plot_data[column], label=column.upper(), linewidth=1.2, color=color)
    ax.set_title(f"{ticker}: Closing Price with Moving Averages")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "actual_price_moving_averages.png", dpi=160)
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    axes[0].plot(plot_data["date"], plot_data["rsi_14"], color="#E45756", linewidth=1.5)
    axes[0].axhline(70, color="#C44E52", linestyle="--", linewidth=1)
    axes[0].axhline(30, color="#4C78A8", linestyle="--", linewidth=1)
    axes[0].set_title(f"{ticker}: RSI")
    axes[0].set_ylabel("RSI")
    axes[0].set_ylim(0, 100)

    colors = ["#54A24B" if value >= 0 else "#E45756" for value in plot_data["macd_hist"].fillna(0)]
    axes[1].plot(plot_data["date"], plot_data["macd"], label="MACD", color="#2F4B7C", linewidth=1.4)
    axes[1].plot(plot_data["date"], plot_data["macd_signal"], label="Signal", color="#F58518", linewidth=1.2)
    axes[1].bar(plot_data["date"], plot_data["macd_hist"], color=colors, alpha=0.45)
    axes[1].axhline(0, color="black", linewidth=0.8)
    axes[1].set_title(f"{ticker}: MACD")
    axes[1].set_xlabel("Date")
    axes[1].set_ylabel("MACD")
    axes[1].legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "actual_rsi_macd.png", dpi=160)
    plt.close(fig)


def save_correlation_plots(merged: pd.DataFrame, returns_by_sentiment: pd.DataFrame, corr: float) -> None:
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.regplot(
        data=merged,
        x="avg_sentiment",
        y="daily_return_pct",
        ax=ax,
        scatter_kws={"alpha": 0.55},
        line_kws={"color": "#E45756"},
    )
    ax.set_title(f"Sentiment vs Daily Return (Pearson r = {corr:.3f})")
    ax.set_xlabel("Average daily sentiment")
    ax.set_ylabel("Daily return (%)")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "actual_sentiment_return_scatter.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    palette = {"negative": "#E45756", "neutral": "#BAB0AC", "positive": "#54A24B"}
    sns.barplot(data=returns_by_sentiment, x="sentiment_label", y="avg_daily_return_pct", ax=ax, hue="sentiment_label", palette=palette, legend=False)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Average Daily Return by Sentiment Category")
    ax.set_xlabel("Sentiment category")
    ax.set_ylabel("Average daily return (%)")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "actual_return_by_sentiment.png", dpi=160)
    plt.close(fig)


def main() -> None:
    ensure_dirs()
    news_path = download_news_sample()
    news = load_news(news_path)
    selected_tickers = news["stock"].value_counts().head(5).index.tolist()

    start = str(pd.to_datetime(news["date"].min()).date() - pd.Timedelta(days=20))
    end = str(pd.to_datetime(news["date"].max()).date() + pd.Timedelta(days=20))
    price_path = download_prices(selected_tickers, start, end)
    prices = clean_price_data(load_price_data(price_path))

    news = news[news["stock"].isin(prices["stock"].unique())].copy()

    length_summary = headline_length_summary(news).round(2)
    top_publishers = top_counts(news, "publisher", n=10)
    top_stocks = top_counts(news, "stock", n=10)
    daily_volume = daily_article_volume(news)
    daily_volume["publication_date"] = pd.to_datetime(daily_volume["publication_date"])
    hourly_volume = hourly_article_volume(news)
    terms = top_tfidf_terms(news["headline"], n=20)

    indicators = add_indicators_by_stock(prices)
    selected_stock = indicators["stock"].value_counts().index[0]
    plot_data = indicators[indicators["stock"] == selected_stock].sort_values("date").copy()
    metrics = compute_pynance_metrics(plot_data).round(4)

    scored = score_headlines(news)
    aligned = align_news_to_trading_day(scored, prices)
    daily_sentiment = aggregate_daily_sentiment(aligned)
    daily_returns = compute_daily_returns(prices)
    merged = merge_sentiment_with_returns(daily_sentiment, daily_returns)
    correlations = pearson_correlation(merged).round(4)
    returns_by_sentiment = average_return_by_sentiment(merged).round(4)
    overall_corr = float(merged["avg_sentiment"].corr(merged["daily_return_pct"], method="pearson")) if len(merged) >= 2 else None

    save_top_publishers(top_publishers)
    save_daily_volume(daily_volume)
    save_terms(terms)
    save_technical_plots(plot_data, selected_stock)
    save_correlation_plots(merged, returns_by_sentiment, overall_corr or 0.0)

    # Persist tables for auditability.
    length_summary.to_csv(PROCESSED_DIR / "headline_length_summary.csv")
    top_publishers.rename("article_count").to_csv(PROCESSED_DIR / "top_publishers.csv")
    top_stocks.rename("article_count").to_csv(PROCESSED_DIR / "top_stocks.csv")
    daily_volume.to_csv(PROCESSED_DIR / "daily_news_volume.csv", index=False)
    hourly_volume.to_csv(PROCESSED_DIR / "hourly_news_volume.csv", index=False)
    terms.to_csv(PROCESSED_DIR / "top_tfidf_terms.csv", index=False)
    metrics.to_csv(PROCESSED_DIR / "financial_metrics.csv", index=False)
    correlations.to_csv(PROCESSED_DIR / "sentiment_return_correlations.csv", index=False)
    returns_by_sentiment.to_csv(PROCESSED_DIR / "returns_by_sentiment.csv", index=False)

    summary = {
        "news_rows": int(len(news)),
        "price_rows": int(len(prices)),
        "date_range": [str(news["date"].min()), str(news["date"].max())],
        "selected_tickers": selected_tickers,
        "top_publishers": top_publishers.to_dict(),
        "top_stocks": top_stocks.to_dict(),
        "headline_mean_chars": float(length_summary.loc["headline_char_count", "mean"]),
        "headline_mean_words": float(length_summary.loc["headline_word_count", "mean"]),
        "peak_news_day": {
            "date": str(daily_volume.sort_values("article_count", ascending=False).iloc[0]["publication_date"].date()),
            "article_count": int(daily_volume["article_count"].max()),
        },
        "peak_news_hour_utc": int(hourly_volume.sort_values("article_count", ascending=False).iloc[0]["publication_hour"]),
        "top_terms": terms.head(10)["term"].tolist(),
        "technical_stock": selected_stock,
        "latest_adj_close": float(plot_data["adj_close"].dropna().iloc[-1]),
        "latest_rsi_14": float(plot_data["rsi_14"].dropna().iloc[-1]),
        "latest_macd": float(plot_data["macd"].dropna().iloc[-1]),
        "financial_metrics": metrics.iloc[0].to_dict(),
        "correlation_observations": int(len(merged)),
        "overall_pearson_correlation": overall_corr,
        "returns_by_sentiment": returns_by_sentiment.to_dict(orient="records"),
        "figures": [
            "actual_top_publishers.png",
            "actual_daily_news_volume.png",
            "actual_top_tfidf_terms.png",
            "actual_price_moving_averages.png",
            "actual_rsi_macd.png",
            "actual_sentiment_return_scatter.png",
            "actual_return_by_sentiment.png",
        ],
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
