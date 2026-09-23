"""Stock data download and technical indicator computation.

Uses yfinance to fetch OHLCV history for Taiwan-listed stocks (ticker suffix
``.TW``) and computes common technical indicators used in equity analysis.
"""

from __future__ import annotations

import pandas as pd
import yfinance as yf

# Mapping of the UI period options to yfinance ``period`` / ``interval`` args.
PERIOD_OPTIONS: dict[str, dict[str, str]] = {
    "日線 (近 3 個月)": {"period": "3mo", "interval": "1d"},
    "日線 (近 6 個月)": {"period": "6mo", "interval": "1d"},
    "日線 (近 1 年)": {"period": "1y", "interval": "1d"},
    "日線 (近 2 年)": {"period": "2y", "interval": "1d"},
    "週線 (近 3 年)": {"period": "3y", "interval": "1wk"},
    "週線 (近 5 年)": {"period": "5y", "interval": "1wk"},
    "月線 (近 5 年)": {"period": "5y", "interval": "1mo"},
    "月線 (近 10 年)": {"period": "10y", "interval": "1mo"},
    "月線 (全部)": {"period": "max", "interval": "1mo"},
}


def normalize_ticker(ticker: str) -> str:
    """Ensure a ticker carries the ``.TW`` suffix for the Taiwan exchange."""
    ticker = ticker.strip().upper()
    if not ticker:
        return ticker
    if ticker.endswith(".TW"):
        return ticker
    return f"{ticker}.TW"


def download_history(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """Download OHLCV history for a single ticker.

    Returns a DataFrame indexed by date with columns Open/High/Low/Close/Volume.
    Returns an empty DataFrame when no data is available.
    """
    ticker = normalize_ticker(ticker)
    tk = yf.Ticker(ticker)
    df = tk.history(period=period, interval=interval, auto_adjust=False)
    if df is None or df.empty:
        return pd.DataFrame()
    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df = df.dropna(subset=["Close"])
    return df


def get_info(ticker: str) -> dict:
    """Fetch a curated subset of fundamental info for a ticker.

    Never raises; returns an empty dict on failure so the UI can degrade
    gracefully.
    """
    ticker = normalize_ticker(ticker)
    try:
        info = yf.Ticker(ticker).info
    except Exception:
        return {}
    if not isinstance(info, dict):
        return {}
    keys =[
        "shortName",
        "longName",
        "sector",
        "industry",
        "marketCap",
        "trailingPE",
        "forwardPE",
        "trailingEps",
        "forwardEps",
        "dividendYield",
        "beta",
        "returnOnEquity",
        "profitMargins",
        "fiftyTwoWeekHigh",
        "fiftyTwoWeekLow",
   ]
    return {k: info.get(k) for k in keys}


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute technical indicators and return a copy of ``df``.

    Adds:
      * Moving averages: MA5, MA10, MA20, MA60
      * Bollinger Bands: BOLL_MID, BOLL_UP, BOLL_LOW
      * MACD: MACD, MACD_SIGNAL, MACD_HIST
      * RSI(14)
    """
    if df is None or df.empty:
        return df

    out = df.copy()
    close = out["Close"]

    # --- Moving averages ---
    for n in (5, 10, 20, 60):
        out[f"MA{n}"] = close.rolling(window=n, min_periods=1).mean()

    # --- Bollinger Bands (20, 2 std) ---
    window = 20
    mid = close.rolling(window=window, min_periods=1).mean()
    std = close.rolling(window=window, min_periods=1).std()
    out["BOLL_MID"] = mid
    out["BOLL_UP"] = mid + 2 * std
    out["BOLL_LOW"] = mid - 2 * std

    # --- MACD (12, 26, 9) ---
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    out["MACD"] = ema12 - ema26
    out["MACD_SIGNAL"] = out["MACD"].ewm(span=9, adjust=False).mean()
    out["MACD_HIST"] = out["MACD"] - out["MACD_SIGNAL"]

    # --- RSI (14) ---
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    out["RSI"] = 100 - (100 / (1 + rs))

    return out


def load_with_indicators(ticker: str, period_key: str) -> pd.DataFrame:
    """Download history for a UI period option and attach indicators."""
    cfg = PERIOD_OPTIONS.get(period_key, {"period": "1y", "interval": "1d"})
    df = download_history(ticker, period=cfg["period"], interval=cfg["interval"])
    if df.empty:
        return df
    return add_indicators(df)