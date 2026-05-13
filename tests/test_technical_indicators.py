import pandas as pd

from src.technical_indicators import (
    add_indicators_by_stock,
    clean_price_data,
    compute_pynance_metrics,
)


def sample_prices() -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=40, freq="D")
    close = pd.Series(range(100, 140), dtype="float")
    return pd.DataFrame(
        {
            "date": dates,
            "stock": ["AAPL"] * len(dates),
            "open": close - 1,
            "high": close + 2,
            "low": close - 2,
            "close": close,
            "adj_close": close,
            "volume": 1_000_000,
        }
    )


def test_add_indicators_by_stock_creates_expected_columns():
    indicators = add_indicators_by_stock(sample_prices())

    expected = {"sma_10", "ema_20", "rsi_14", "macd", "macd_signal", "macd_hist"}
    assert expected.issubset(indicators.columns)
    assert indicators["daily_return"].notna().sum() > 0


def test_clean_price_data_fills_numeric_gaps():
    prices = sample_prices()
    prices.loc[3, "close"] = None
    prices.loc[3, "adj_close"] = None

    cleaned = clean_price_data(prices)

    assert cleaned[["close", "adj_close"]].isna().sum().sum() == 0


def test_compute_pynance_metrics_returns_core_metrics():
    metrics = compute_pynance_metrics(sample_prices())

    assert "cumulative_return" in metrics.columns
    assert metrics.loc[0, "end_price"] > metrics.loc[0, "start_price"]
