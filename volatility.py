from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def log_returns(prices: pd.Series) -> pd.Series:
    returns = np.log(prices / prices.shift(1))
    return returns.dropna()


def annualized_historical_volatility(prices: pd.Series, trading_days: int = TRADING_DAYS) -> float:
    rets = log_returns(prices)
    if rets.empty:
        return float("nan")
    return float(rets.std(ddof=1) * np.sqrt(trading_days))


def rolling_annualized_volatility(
    prices: pd.Series,
    windows: tuple[int, ...] = (20, 60, 120),
    trading_days: int = TRADING_DAYS,
) -> pd.DataFrame:
    rets = log_returns(prices)
    out = pd.DataFrame(index=rets.index)
    for w in windows:
        out[f"rolling_vol_{w}d"] = rets.rolling(window=w).std(ddof=1) * np.sqrt(trading_days)
    return out


def ewma_volatility(
    prices: pd.Series,
    lambda_: float = 0.94,
    trading_days: int = TRADING_DAYS,
) -> pd.Series:
    if not 0 < lambda_ < 1:
        raise ValueError("lambda_ must be in (0, 1)")

    rets = log_returns(prices)
    if rets.empty:
        return pd.Series(dtype=float)

    alpha = 1 - lambda_
    var = rets.pow(2).ewm(alpha=alpha, adjust=False).mean()
    vol = np.sqrt(var) * np.sqrt(trading_days)
    vol.name = f"ewma_vol_lambda_{lambda_}"
    return vol


def summarize_volatility(prices: pd.Series) -> pd.DataFrame:
    hist = annualized_historical_volatility(prices)
    rolling = rolling_annualized_volatility(prices)
    ewma = ewma_volatility(prices)

    summary = {
        "historical_vol": hist,
        "rolling_20d_latest": rolling["rolling_vol_20d"].dropna().iloc[-1] if not rolling.empty else np.nan,
        "rolling_60d_latest": rolling["rolling_vol_60d"].dropna().iloc[-1] if not rolling.empty else np.nan,
        "rolling_120d_latest": rolling["rolling_vol_120d"].dropna().iloc[-1] if not rolling.empty else np.nan,
        "ewma_latest": ewma.dropna().iloc[-1] if not ewma.empty else np.nan,
    }
    return pd.DataFrame([summary])
