from __future__ import annotations

from pathlib import Path

import pandas as pd

from .volatility import log_returns


def load_macro_events(csv_path: str | Path) -> pd.DataFrame:
    events = pd.read_csv(csv_path)
    required = {"event_date", "event_name"}
    missing = required - set(events.columns)
    if missing:
        raise ValueError(f"Event file missing required columns: {sorted(missing)}")

    out = events[["event_date", "event_name"]].copy()
    out["event_date"] = pd.to_datetime(out["event_date"], utc=False)
    out = out.dropna(subset=["event_date", "event_name"])
    out = out.sort_values("event_date")
    return out


def _realized_vol_from_returns(returns: pd.Series, annualization_factor: int = 252) -> float:
    if returns.empty:
        return float("nan")
    return float(returns.std(ddof=1) * (annualization_factor**0.5))


def compare_event_volatility(
    prices: pd.Series,
    events: pd.DataFrame,
    window_days: int = 10,
    annualization_factor: int = 252,
) -> pd.DataFrame:
    rets = log_returns(prices)
    if rets.empty:
        raise ValueError("Not enough price points to compute returns")

    records: list[dict[str, object]] = []
    for _, row in events.iterrows():
        event_day = pd.Timestamp(row["event_date"])

        pre_window = rets.loc[(rets.index < event_day) & (rets.index >= event_day - pd.Timedelta(days=window_days))]
        post_window = rets.loc[
            (rets.index >= event_day) & (rets.index < event_day + pd.Timedelta(days=window_days))
        ]

        pre_vol = _realized_vol_from_returns(pre_window, annualization_factor)
        post_vol = _realized_vol_from_returns(post_window, annualization_factor)

        records.append(
            {
                "event_name": row["event_name"],
                "event_date": event_day,
                "pre_realized_vol": pre_vol,
                "post_realized_vol": post_vol,
                "vol_change": post_vol - pre_vol,
                "vol_ratio": (post_vol / pre_vol) if pre_vol and pre_vol > 0 else float("nan"),
                "pre_obs": int(pre_window.shape[0]),
                "post_obs": int(post_window.shape[0]),
            }
        )

    return pd.DataFrame(records).sort_values("event_date")
