# Predicting Price Moves with News Sentiment

## Executive Summary

This final report presents completed evidence for the Nova Financial Solutions challenge. The project now includes actual exploratory data analysis, price-based technical indicator analysis, and sentiment-return correlation analysis.

The analysis uses a reproducible streamed sample of the public FNSPID news dataset and matching Yahoo Finance daily price data. It generated concrete tables and figures under `data/processed/` and `reports/figures/`.

## Data Used

- FNSPID news sample: 2,493 rows.
- Historical stock prices: 17,784 rows.
- Stocks analyzed: AA, AAL, A, AADR, AACG.
- News date range: 2009-10-07 to 2023-12-16.

## Task 1: EDA Findings

The average headline length was 60.20 characters and 9.78 words. The busiest news day in the sample was 2023-05-24 with 21 articles. The most common publishing hour was 00:00 UTC.

Top covered stocks were AA, AAL, A, AADR, and AACG. Top TF-IDF terms included alcoa, earnings, aa, stock, stocks, market, analyst, analyst blog, blog, and alcoa aa.

Generated figures:

- `actual_top_publishers.png`
- `actual_daily_news_volume.png`
- `actual_top_tfidf_terms.png`

## Task 2: Technical Indicator Findings

The price analysis computed SMA, EMA, RSI, MACD, daily returns, cumulative return, annualized volatility, max drawdown, and Sharpe ratio.

For the selected technical-analysis stock A:

- Latest adjusted close: 128.76.
- Latest RSI(14): 47.68.
- Latest MACD: 3.333.
- Cumulative return: 6.14.
- Annualized volatility: 0.29.
- Maximum drawdown: -0.44.
- Sharpe ratio: 0.62.

Generated figures:

- `actual_price_moving_averages.png`
- `actual_rsi_macd.png`

## Task 3: Sentiment and Return Correlation

The sentiment-return dataset contained 1,227 matched stock-day observations after aligning headlines to valid trading days and joining them with daily adjusted-close returns.

The overall Pearson correlation between average daily sentiment and daily return was 0.039. This indicates a weak same-day linear relationship in the sampled data.

Average return by sentiment category:

- Negative: 0.36% over 191 observations.
- Neutral: 0.16% over 565 observations.
- Positive: 2.23% over 471 observations.

Generated figures:

- `actual_sentiment_return_scatter.png`
- `actual_return_by_sentiment.png`

## Investment Recommendations

Headline sentiment should be used as a supporting feature rather than a standalone trading signal. The weak same-day Pearson correlation suggests sentiment alone is not enough for robust prediction.

Positive sentiment showed stronger average returns than neutral and negative days in the sampled data, so sentiment may still be useful when combined with technical confirmation such as improving MACD, supportive moving averages, and adequate liquidity.

Further strategy development should segment headlines by event type, compare same-day and lagged return windows, and validate signals out of sample.

## Limitations

The public FNSPID news file is extremely large, so the current evidence uses a reproducible streamed sample. Correlation does not prove causation, and same-day returns may miss delayed market reactions. After-hours news should be modeled separately in a more advanced event-study design.
