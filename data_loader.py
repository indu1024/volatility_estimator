from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class PriceSeries:
    symbol: str
    prices: pd.Series


def _validate_price_frame(df: pd.DataFrame) -> pd.DataFrame:
    required = {"Date", "Close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Price data missing required columns: {sorted(missing)}")

    clean = df[["Date", "Close"]].copy()
    clean["Date"] = pd.to_datetime(clean["Date"], utc=False)
    clean = clean.dropna(subset=["Date", "Close"])
    clean = clean.sort_values("Date")
    clean = clean.drop_duplicates(subset=["Date"], keep="last")
    return clean


def load_prices_from_csv(csv_path: str | Path, symbol: str = "ASSET") -> PriceSeries:
    df = pd.read_csv(csv_path)
    clean = _validate_price_frame(df)
    series = clean.set_index("Date")["Close"].astype(float)
    return PriceSeries(symbol=symbol, prices=series)


def load_prices_from_yfinance(symbol: str, start: str, end: str | None = None) -> PriceSeries:
    try:
        import yfinance as yf
    except ImportError as exc:
        raise ImportError(
            "yfinance is required for --source yfinance. Install with: pip install .[market]"
        ) from exc

    df = yf.download(symbol, start=start, end=end, auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"No data returned from yfinance for {symbol}")

    out = pd.DataFrame(
        {
            "Date": df.index,
            "Close": df["Close"],
        }
    )
    clean = _validate_price_frame(out)
    series = clean.set_index("Date")["Close"].astype(float)
    return PriceSeries(symbol=symbol, prices=series)
