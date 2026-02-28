import numpy as np
import pandas as pd

from volatility_estimator.events import compare_event_volatility
from volatility_estimator.report import generate_markdown_report
from volatility_estimator.volatility import (
    annualized_historical_volatility,
    ewma_volatility,
    rolling_annualized_volatility,
)


def _sample_prices() -> pd.Series:
    idx = pd.bdate_range("2024-01-01", periods=200)
    rng = np.random.default_rng(42)
    rets = rng.normal(0.0002, 0.01, size=len(idx))
    px = 100 * np.exp(np.cumsum(rets))
    return pd.Series(px, index=idx, name="Close")


def test_historical_vol_is_positive() -> None:
    prices = _sample_prices()
    vol = annualized_historical_volatility(prices)
    assert vol > 0


def test_rolling_windows_exist() -> None:
    prices = _sample_prices()
    rolling = rolling_annualized_volatility(prices)
    assert {"rolling_vol_20d", "rolling_vol_60d", "rolling_vol_120d"}.issubset(rolling.columns)


def test_ewma_non_empty_and_positive() -> None:
    prices = _sample_prices()
    ewma = ewma_volatility(prices, lambda_=0.94)
    assert not ewma.empty
    assert ewma.dropna().iloc[-1] > 0


def test_event_comparison_shape() -> None:
    prices = _sample_prices()
    events = pd.DataFrame(
        {
            "event_date": ["2024-03-01", "2024-05-15"],
            "event_name": ["CPI", "FOMC"],
        }
    )
    events["event_date"] = pd.to_datetime(events["event_date"])

    out = compare_event_volatility(prices, events, window_days=10)

    assert out.shape[0] == 2
    assert {"pre_realized_vol", "post_realized_vol", "vol_change", "vol_ratio"}.issubset(out.columns)


def test_markdown_report_generation(tmp_path) -> None:
    summary = pd.DataFrame(
        [
            {
                "historical_vol": 0.15,
                "rolling_20d_latest": 0.18,
                "rolling_60d_latest": 0.17,
                "rolling_120d_latest": 0.16,
                "ewma_latest": 0.19,
            }
        ]
    )
    events = pd.DataFrame(
        {
            "event_name": ["CPI", "FOMC"],
            "event_date": pd.to_datetime(["2024-03-01", "2024-05-15"]),
            "pre_realized_vol": [0.13, 0.14],
            "post_realized_vol": [0.18, 0.11],
            "vol_change": [0.05, -0.03],
        }
    )

    path = generate_markdown_report(
        symbol="SPY",
        summary_df=summary,
        event_df=events,
        output_dir=tmp_path,
    )
    content = path.read_text(encoding="utf-8")
    assert path.exists()
    assert "SPY Volatility Report" in content
    assert "Largest vol increase event" in content
