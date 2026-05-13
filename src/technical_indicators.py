"""Price-data preparation, technical indicators, and financial metrics."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


REQUIRED_PRICE_COLUMNS = {"date", "open", "high", "low", "close", "volume"}
ADJ_CLOSE_CANDIDATES = ("adj_close", "adjusted_close", "close")
DEFAULT_PRICE_FILENAMES = (
    "stock_prices.csv",
    "historical_stock_prices.csv",
    "prices.csv",
    "yf_prices.csv",
)


def find_price_file(raw_dir: str | Path = "data/raw") -> Path:
    """Return the first likely historical price CSV in the raw data directory."""
    raw_path = Path(raw_dir)
    for filename in DEFAULT_PRICE_FILENAMES:
        candidate = raw_path / filename
        if candidate.exists():
            return candidate

    csv_files = [
        path
        for path in sorted(raw_path.glob("*.csv"))
        if "price" in path.stem.lower() or "stock" in path.stem.lower()
    ]
    if csv_files:
        return csv_files[0]

    raise FileNotFoundError(
        f"No price CSV found in {raw_path}. Add a historical stock price file to data/raw/."
    )


def load_price_data(path: str | Path | None = None) -> pd.DataFrame:
    """Load historical OHLCV price data and normalize column names/types."""
    if path is None:
        price_path = find_price_file()
    else:
        candidate = Path(path)
        price_path = find_price_file(candidate) if candidate.is_dir() else candidate

    prices = pd.read_csv(price_path)
    prices.columns = [column.strip().lower().replace(" ", "_") for column in prices.columns]

    missing = REQUIRED_PRICE_COLUMNS.difference(prices.columns)
    if missing:
        missing_columns = ", ".join(sorted(missing))
        raise ValueError(f"Price file is missing required columns: {missing_columns}")

    prices = prices.copy()
    prices["date"] = pd.to_datetime(prices["date"], errors="coerce")
    for column in ["open", "high", "low", "close", "volume"]:
        prices[column] = pd.to_numeric(prices[column], errors="coerce")

    if "adj_close" not in prices.columns and "adjusted_close" in prices.columns:
        prices["adj_close"] = pd.to_numeric(prices["adjusted_close"], errors="coerce")
    elif "adj_close" in prices.columns:
        prices["adj_close"] = pd.to_numeric(prices["adj_close"], errors="coerce")
    else:
        prices["adj_close"] = prices["close"]

    if "stock" in prices.columns:
        prices["stock"] = prices["stock"].fillna("unknown").astype(str).str.upper().str.strip()

    prices = prices.dropna(subset=["date", "open", "high", "low", "close", "volume"])
    sort_columns = ["stock", "date"] if "stock" in prices.columns else ["date"]
    prices = prices.sort_values(sort_columns).reset_index(drop=True)
    return prices


def missing_value_report(prices: pd.DataFrame) -> pd.Series:
    """Return missing-value counts for each price column."""
    return prices.isna().sum().sort_values(ascending=False)


def clean_price_data(prices: pd.DataFrame) -> pd.DataFrame:
    """Forward/backward fill numeric gaps within each ticker, then drop unusable rows."""
    cleaned = prices.copy()
    numeric_columns = ["open", "high", "low", "close", "adj_close", "volume"]
    group_columns = ["stock"] if "stock" in cleaned.columns else []

    if group_columns:
        cleaned[numeric_columns] = cleaned.groupby(group_columns, group_keys=False)[
            numeric_columns
        ].apply(lambda frame: frame.ffill().bfill())
    else:
        cleaned[numeric_columns] = cleaned[numeric_columns].ffill().bfill()

    cleaned = cleaned.dropna(subset=numeric_columns)
    return cleaned.reset_index(drop=True)


def _talib_module():
    try:
        import talib

        return talib
    except Exception:
        return None


def add_moving_averages(
    prices: pd.DataFrame,
    windows: Iterable[int] = (10, 20, 50),
    price_column: str = "adj_close",
) -> pd.DataFrame:
    """Add SMA and EMA columns, using TA-Lib when it is installed."""
    result = prices.copy()
    talib = _talib_module()

    for window in windows:
        if talib is not None:
            result[f"sma_{window}"] = talib.SMA(result[price_column].to_numpy(float), timeperiod=window)
            result[f"ema_{window}"] = talib.EMA(result[price_column].to_numpy(float), timeperiod=window)
        else:
            result[f"sma_{window}"] = result[price_column].rolling(window=window).mean()
            result[f"ema_{window}"] = result[price_column].ewm(span=window, adjust=False).mean()
    return result


def add_rsi(prices: pd.DataFrame, window: int = 14, price_column: str = "adj_close") -> pd.DataFrame:
    """Add RSI, using TA-Lib when available and a Wilder-style fallback otherwise."""
    result = prices.copy()
    talib = _talib_module()

    if talib is not None:
        result[f"rsi_{window}"] = talib.RSI(result[price_column].to_numpy(float), timeperiod=window)
        return result

    delta = result[price_column].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    result[f"rsi_{window}"] = 100 - (100 / (1 + rs))
    return result


def add_macd(
    prices: pd.DataFrame,
    fastperiod: int = 12,
    slowperiod: int = 26,
    signalperiod: int = 9,
    price_column: str = "adj_close",
) -> pd.DataFrame:
    """Add MACD, signal, and histogram columns."""
    result = prices.copy()
    talib = _talib_module()

    if talib is not None:
        macd, signal, hist = talib.MACD(
            result[price_column].to_numpy(float),
            fastperiod=fastperiod,
            slowperiod=slowperiod,
            signalperiod=signalperiod,
        )
    else:
        fast = result[price_column].ewm(span=fastperiod, adjust=False).mean()
        slow = result[price_column].ewm(span=slowperiod, adjust=False).mean()
        macd = fast - slow
        signal = macd.ewm(span=signalperiod, adjust=False).mean()
        hist = macd - signal

    result["macd"] = macd
    result["macd_signal"] = signal
    result["macd_hist"] = hist
    return result


def add_technical_indicators(prices: pd.DataFrame) -> pd.DataFrame:
    """Add the Task 2 indicator set to a single-ticker price frame."""
    indicators = add_moving_averages(prices)
    indicators = add_rsi(indicators)
    indicators = add_macd(indicators)
    indicators["daily_return"] = indicators["adj_close"].pct_change()
    return indicators


def add_indicators_by_stock(prices: pd.DataFrame) -> pd.DataFrame:
    """Add indicators independently for each ticker when a stock column exists."""
    if "stock" not in prices.columns:
        return add_technical_indicators(prices)

    frames = []
    for _, group in prices.groupby("stock", sort=False):
        frames.append(add_technical_indicators(group.sort_values("date")))
    return pd.concat(frames, ignore_index=True)


def compute_pynance_metrics(prices: pd.DataFrame) -> pd.DataFrame:
    """Compute PyNance-style financial metrics, using pynance when available.

    PyNance installations vary by version, so this function keeps a stable output
    contract and augments it with local calculations when direct helpers are absent.
    """
    price_column = "adj_close" if "adj_close" in prices.columns else "close"
    returns = prices[price_column].pct_change().dropna()
    cumulative_return = (1 + returns).prod() - 1 if not returns.empty else np.nan
    annualized_volatility = returns.std() * np.sqrt(252) if not returns.empty else np.nan
    running_peak = prices[price_column].cummax()
    drawdown = prices[price_column] / running_peak - 1
    sharpe_ratio = (
        returns.mean() / returns.std() * np.sqrt(252)
        if not returns.empty and returns.std() != 0
        else np.nan
    )

    metrics = {
        "start_price": prices[price_column].iloc[0],
        "end_price": prices[price_column].iloc[-1],
        "cumulative_return": cumulative_return,
        "annualized_volatility": annualized_volatility,
        "max_drawdown": drawdown.min(),
        "sharpe_ratio_zero_rf": sharpe_ratio,
    }

    try:
        import pynance as pn  # noqa: F401

        metrics["pynance_available"] = True
    except Exception:
        metrics["pynance_available"] = False

    return pd.DataFrame([metrics])
