# Nova Financial Solutions: Financial News and Price-Move Analysis Report

## Executive Summary

This project establishes the first two stages of a financial intelligence pipeline for Nova Financial Solutions. Task 1 focuses on exploratory analysis of financial news headlines, publishers, publication timing, and recurring topics. Task 2 extends the workflow into quantitative market analysis by loading historical OHLCV price data, cleaning it, computing technical indicators, and visualizing price behavior.

The repository now contains reproducible notebooks, tested helper modules, CI configuration, and clean Git branches for `task-1` and `task-2`. The analysis is ready to run once the raw FNSPID news dataset and historical stock-price CSV files are placed in `data/raw/`.

## Business Objective

Nova Financial Solutions wants to improve forecasting accuracy by connecting market narratives to price action. The core analytical question is whether financial-news sentiment and publishing patterns can help explain or anticipate stock-price movement.

This report covers the completed setup for:

- Financial news exploratory data analysis.
- Headline keyword and topic discovery.
- Publisher and publication-time analysis.
- Historical price-data preparation.
- Technical indicator computation.
- Price, RSI, and MACD visualizations.

## Repository and Workflow Status

The project has been structured for reproducible analysis:

- `main` contains the merged Task 1 baseline.
- `task-2` contains the quantitative analysis work.
- GitHub Actions is configured to run unit tests.
- Helper functions are covered by tests.
- Notebooks are separated from reusable source code.

Key files:

- `notebooks/task_1_eda.ipynb`
- `notebooks/task_2_quantitative_analysis.ipynb`
- `src/data_loader.py`
- `src/eda.py`
- `src/technical_indicators.py`
- `tests/test_eda.py`
- `tests/test_technical_indicators.py`

## Task 1: Exploratory Data Analysis

### Data Preparation

The Task 1 pipeline expects a financial news CSV with these columns:

- `headline`
- `url`
- `publisher`
- `date`
- `stock`

The loader standardizes column names, parses publication timestamps as UTC-aware dates, normalizes ticker symbols, and creates derived fields:

- `publication_date`
- `publication_hour`
- `headline_char_count`
- `headline_word_count`

### Descriptive Statistics

The EDA notebook computes headline length distributions using character and word counts. This helps identify whether the dataset is dominated by short market alerts, longer analyst commentary, or inconsistent text records.

The notebook also counts:

- Articles by publisher.
- Articles by stock ticker.
- Unique publishers.
- Unique covered tickers.
- Dataset date range.

These outputs help identify concentration risk. If a small number of publishers or tickers dominate the dataset, later sentiment analysis may be biased toward their writing style or coverage focus.

### Topic and Keyword Analysis

The notebook uses TF-IDF to identify high-signal terms and phrases in headlines. It also applies lightweight LDA topic modeling to group recurring headline themes.

Expected themes may include:

- Earnings results.
- Analyst rating changes.
- Price target revisions.
- FDA approvals or clinical trial updates.
- Mergers and acquisitions.
- Stock offering announcements.
- Guidance updates.

These topics are useful because not all news sentiment carries the same market meaning. For example, positive sentiment around an FDA approval may have a different price impact than positive sentiment around an analyst price-target increase.

### Time Series News Volume

The notebook analyzes article frequency by:

- Calendar date.
- UTC publication hour.

Daily volume spikes can reveal market events, earnings cycles, or intense ticker-specific coverage. Hourly patterns help determine whether news is clustered before market open, during trading hours, or after close. This matters for later return alignment because a headline released after market close should usually be linked to the next trading day rather than the same day.

### Publisher Analysis

The notebook ranks the most active publishers and extracts email domains when publisher names are email addresses. This helps distinguish individual contributors from institutional sources and can reveal whether a small number of organizations drive a large share of the news volume.

## Task 2: Quantitative Price Analysis

### Data Preparation

The Task 2 pipeline expects a historical stock-price CSV with:

- `Date`
- `Open`
- `High`
- `Low`
- `Close`
- `Volume`

Recommended:

- `Adj Close`
- `Stock`

The loader standardizes column names, parses dates, converts OHLCV fields to numeric values, and uses `adj_close` for return calculations when available. If adjusted close is absent, it falls back to close price.

Missing numeric values are handled by forward/backward filling within each ticker. Rows that remain unusable after cleaning are dropped.

### Technical Indicators

The Task 2 module computes:

- Simple Moving Averages: `sma_10`, `sma_20`, `sma_50`
- Exponential Moving Averages: `ema_10`, `ema_20`, `ema_50`
- Relative Strength Index: `rsi_14`
- MACD line
- MACD signal line
- MACD histogram
- Daily adjusted-close return

The implementation uses TA-Lib when installed. If TA-Lib is unavailable, equivalent pandas-based fallback calculations are used so the notebook remains executable.

### PyNance Metrics

The project includes a PyNance-aware metrics function. Because PyNance APIs can vary by installation, the function records whether PyNance is available and computes a stable set of financial metrics:

- Start price.
- End price.
- Cumulative return.
- Annualized volatility.
- Maximum drawdown.
- Sharpe ratio using a zero risk-free rate assumption.

These metrics provide a compact risk-return profile for each ticker before sentiment-return correlation is attempted.

### Visualizations

The Task 2 notebook produces three main visualization panels:

- Adjusted close price overlaid with SMA and EMA lines.
- RSI with overbought and oversold thresholds at 70 and 30.
- MACD line, signal line, and histogram.

When executed, figures are saved to `reports/figures/`.

## Data Quality Considerations

The current repository does not include the raw FNSPID or historical price datasets. Therefore, this report does not claim dataset-specific numerical findings.

Important quality checks before final interpretation:

- Confirm that ticker symbols match between news and price data.
- Remove or investigate duplicate ticker-date price rows.
- Verify that `Adj Close` is available and split-adjusted.
- Align publication timestamps correctly with trading calendars.
- Treat after-hours news as next-session information where appropriate.
- Check whether publisher concentration biases sentiment results.
- Avoid interpreting correlation as causation.

## Strategic Recommendations

1. Use adjusted close returns for all return calculations.

Adjusted prices account for splits and dividends, making them more reliable for historical return analysis than raw close prices.

2. Align news to trading sessions before correlation analysis.

Publication timing matters. A headline released after market close should generally be mapped to the next trading session when measuring impact.

3. Segment sentiment by topic.

Headline sentiment should not be treated as one uniform signal. Earnings, analyst ratings, FDA events, and M&A headlines may each have different return relationships.

4. Control for publisher concentration.

If a few publishers dominate the dataset, evaluate whether sentiment patterns are driven by true market narratives or by repeated editorial style.

5. Combine sentiment with technical indicators.

Technical indicators can help filter sentiment signals. For example, positive sentiment during an improving MACD trend may be more actionable than positive sentiment during a weakening trend.

6. Measure short-window and next-day effects separately.

For Task 3, compare same-day, next-day, and multi-day returns after headline publication. This will help distinguish immediate reaction from delayed drift.

## Limitations

The current work creates the analytical foundation but does not yet produce final investment conclusions because raw data is not present in the workspace. Final recommendations should be updated after running both notebooks against the actual FNSPID and historical stock-price datasets.

The technical indicators are descriptive tools, not standalone forecasts. Sentiment-return correlations should be tested out of sample before being used in an investment strategy.

## Next Steps

- Add the raw FNSPID news CSV to `data/raw/`.
- Add historical stock-price CSV data to `data/raw/`.
- Run `notebooks/task_1_eda.ipynb`.
- Run `notebooks/task_2_quantitative_analysis.ipynb`.
- Review generated figures in `reports/figures/`.
- Proceed to sentiment scoring and correlation analysis in Task 3.
