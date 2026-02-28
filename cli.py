from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .data_loader import load_prices_from_csv, load_prices_from_yfinance
from .events import compare_event_volatility, load_macro_events
from .report import build_report
from .volatility import ewma_volatility, rolling_annualized_volatility, summarize_volatility


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compute historical, rolling, and EWMA volatility and compare realized volatility "
            "before/after macro events."
        )
    )
    parser.add_argument("--symbol", required=True, help="Ticker/symbol label, e.g., SPY")
    parser.add_argument(
        "--source",
        choices=["csv", "yfinance"],
        default="csv",
        help="Price data source",
    )
    parser.add_argument(
        "--prices-csv",
        type=Path,
        help="Path to CSV with columns Date,Close (required when --source=csv)",
    )
    parser.add_argument("--start", help="Start date for yfinance, e.g., 2020-01-01")
    parser.add_argument("--end", help="End date for yfinance (optional)")
    parser.add_argument(
        "--events-csv",
        type=Path,
        required=True,
        help="Path to macro events CSV with columns event_date,event_name",
    )
    parser.add_argument(
        "--event-window-days",
        type=int,
        default=10,
        help="Calendar-day window for before/after event realized vol comparison",
    )
    parser.add_argument(
        "--ewma-lambda",
        type=float,
        default=0.94,
        help="EWMA decay parameter lambda (0,1)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory to write output CSV files",
    )
    parser.add_argument(
        "--skip-report",
        action="store_true",
        help="Skip generating plots and markdown report",
    )
    return parser.parse_args()


def _load_prices(args: argparse.Namespace) -> pd.Series:
    if args.source == "csv":
        if args.prices_csv is None:
            raise ValueError("--prices-csv is required when --source=csv")
        return load_prices_from_csv(args.prices_csv, args.symbol).prices

    if not args.start:
        raise ValueError("--start is required when --source=yfinance")
    return load_prices_from_yfinance(args.symbol, start=args.start, end=args.end).prices


def main() -> None:
    args = parse_args()

    prices = _load_prices(args)
    events = load_macro_events(args.events_csv)

    summary = summarize_volatility(prices)
    rolling = rolling_annualized_volatility(prices)
    ewma = ewma_volatility(prices, lambda_=args.ewma_lambda)

    event_comparison = compare_event_volatility(
        prices=prices,
        events=events,
        window_days=args.event_window_days,
    )

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_path = out_dir / f"{args.symbol}_vol_summary.csv"
    series_path = out_dir / f"{args.symbol}_vol_series.csv"
    event_path = out_dir / f"{args.symbol}_event_vol_comparison.csv"

    vol_series = rolling.join(ewma, how="outer")
    summary.to_csv(summary_path, index=False)
    vol_series.to_csv(series_path)
    event_comparison.to_csv(event_path, index=False)

    report_outputs: dict[str, Path | None] = {}
    if not args.skip_report:
        try:
            report_outputs = build_report(
                symbol=args.symbol,
                summary_df=summary,
                vol_series=vol_series,
                event_df=event_comparison,
                output_dir=out_dir,
            )
        except ImportError as exc:
            print(f"Report generation skipped (missing dependency): {exc}")

    print(f"Saved summary: {summary_path}")
    print(f"Saved volatility series: {series_path}")
    print(f"Saved event comparison: {event_path}")
    if report_outputs:
        print(f"Saved volatility plot: {report_outputs['vol_plot']}")
        print(f"Saved event plot: {report_outputs['event_plot']}")
        print(f"Saved markdown report: {report_outputs['report']}")
    print("\nLatest summary:")
    print(summary.to_string(index=False))
    print("\nEvent comparison preview:")
    print(event_comparison.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
