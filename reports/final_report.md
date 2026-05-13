# Predicting Price Moves with News Sentiment

## Executive Summary

Nova Financial Solutions needs a repeatable way to separate meaningful market narrative from noisy headline flow. This project builds that foundation in three stages: exploratory analysis of financial news, quantitative analysis of historical stock prices, and statistical linkage between headline sentiment and daily returns.

The repository now contains a complete analysis pipeline with reproducible notebooks, reusable Python modules, tests, and GitHub-ready branch structure. The work is designed to run once the FNSPID news CSV and historical stock-price CSV files are placed in `data/raw/`.

Because the raw datasets are not included in the workspace, this report focuses on methodology, outputs, interpretation framework, and investment strategy logic rather than fabricated numerical findings.

## Methodology

### Task 1: News Exploratory Data Analysis

The first notebook profiles the FNSPID-style news dataset. It standardizes the required fields: `headline`, `url`, `publisher`, `date`, and `stock`. Publication dates are parsed with timezone awareness, ticker symbols are normalized, and derived fields are created for publication day, publication hour, headline character count, and headline word count.

The EDA workflow covers:

- Headline length distributions.
- Article counts by publisher.
- Article counts by stock ticker.
- Publication frequency by date.
- Publication frequency by hour.
- Publisher email-domain extraction.
- TF-IDF keyword and phrase extraction.
- LDA topic modeling for recurring headline themes.

This identifies whether the dataset is concentrated around a few tickers or publishers and reveals common market-moving themes such as earnings, analyst ratings, price targets, clinical events, M&A, and guidance updates.

### Task 2: Technical Indicator and Price Analysis

The second notebook loads historical OHLCV price data, validates numeric types, handles missing values, and computes technical indicators. Adjusted close is preferred for return calculations because it accounts for stock splits and dividends.

The indicator pipeline computes:

- Simple Moving Averages over multiple windows.
- Exponential Moving Averages over multiple windows.
- RSI for overbought and oversold conditions.
- MACD, signal line, and histogram for momentum shifts.
- Daily adjusted-close returns.

TA-Lib is used when installed. Since TA-Lib can require native binaries, the project also includes pandas-based fallbacks so the notebook remains reproducible across environments.

PyNance availability is checked, and the pipeline computes additional financial metrics:

- Cumulative return.
- Annualized volatility.
- Maximum drawdown.
- Zero-risk-free-rate Sharpe ratio.

The notebook produces three core visualizations:

- Closing price with moving averages.
- RSI with overbought and oversold thresholds.
- MACD with signal line and histogram.

### Task 3: Sentiment and Return Correlation

The third notebook links average daily headline sentiment to stock returns. It scores each headline, aligns publication dates to valid trading days, aggregates sentiment by ticker/date, calculates daily returns, and measures Pearson correlation.

VADER is selected as the primary sentiment tool because financial headlines are short, polarity-heavy text snippets. VADER provides a normalized compound score that is easy to aggregate and interpret. A lightweight lexicon fallback is included so tests and basic runs remain reproducible if optional NLP packages are unavailable.

The Task 3 workflow covers:

- Headline sentiment scoring.
- Positive, neutral, and negative sentiment classification.
- Weekend and holiday alignment to the next available trading day.
- Daily return calculation using adjusted close.
- Average daily sentiment aggregation for multiple same-day articles.
- Pearson correlation between sentiment and daily return.
- Scatter plot of sentiment versus return.
- Bar chart of average return by sentiment category.

## Interpretation Framework

A positive Pearson coefficient means higher sentiment tends to coincide with higher daily returns. A negative coefficient means higher sentiment tends to coincide with lower daily returns. A coefficient near zero suggests weak same-day linear association.

Interpretation should consider sample size. A ticker with only a handful of sentiment-return matches should not drive strategy decisions. Correlation should also be reviewed by topic: earnings headlines, analyst-rating headlines, FDA headlines, and M&A headlines may behave differently.

The sentiment-category bar chart provides a simpler stakeholder view: if positive sentiment days show higher average returns than neutral and negative days, sentiment may contain tradable signal. If the categories overlap heavily, sentiment may be too noisy in aggregate and should be segmented by event type, sector, or lag window.

## Investment Strategy Recommendations

1. Use sentiment as a feature, not a standalone signal.

Headline sentiment should be combined with price momentum, volatility, liquidity, and event type. A positive headline during improving MACD momentum may be more actionable than a positive headline during a weakening trend.

2. Align news to trading sessions carefully.

Weekend and holiday articles should map to the next trading day. After-hours articles should be tested separately because same-day returns may not reflect the market reaction.

3. Segment by headline topic.

Aggregate sentiment may hide useful signals. Analyst upgrades, earnings beats, regulatory approvals, and acquisition news can produce different return patterns.

4. Control for publisher concentration.

If a small number of publishers dominate coverage, the model may learn writing style rather than market signal. Publisher-level diagnostics should be part of feature validation.

5. Test multiple return windows.

Same-day correlation is only one view. The next step should compare same-day, next-day, three-day, and five-day forward returns to detect delayed drift.

6. Prefer risk-adjusted evaluation.

Any candidate strategy should be evaluated with volatility, drawdown, and Sharpe ratio, not only raw return.

## Limitations

This pipeline measures statistical association, not causation. Stock returns can be driven by earnings, macroeconomic releases, sector shocks, liquidity, analyst behavior, and broad market movement. Sentiment may react to price movement rather than predict it.

The analysis also depends on timestamp quality. If news timestamps are inconsistent or missing timezone information, event alignment can introduce bias. Similarly, adjusted close quality is essential for reliable return calculations.

Finally, sentiment models can misread financial language. A word like "beat" is usually positive in earnings context, while "cut" may refer to costs, rates, or price targets. Topic-aware sentiment analysis would improve precision.

## Next Steps

- Add the raw FNSPID news dataset to `data/raw/`.
- Add historical stock-price CSV files to `data/raw/`.
- Run all three notebooks in sequence.
- Export generated plots from `reports/figures/`.
- Compare same-day and lagged sentiment-return correlations.
- Segment results by stock, publisher, sector, and topic.
- Validate any signal out of sample before recommending live use.
