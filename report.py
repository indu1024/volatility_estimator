from __future__ import annotations

from pathlib import Path

import pandas as pd


def _format_pct(x: float) -> str:
    if pd.isna(x):
        return "NA"
    return f"{x:.2%}"


def _top_event_line(event_df: pd.DataFrame, column: str, largest: bool = True) -> str:
    if event_df.empty or column not in event_df:
        return "NA"
    clean = event_df.dropna(subset=[column])
    if clean.empty:
        return "NA"
    row = clean.sort_values(column, ascending=not largest).iloc[0]
    return f"{row['event_name']} ({row['event_date'].date()}): {row[column]:.4f}"


def plot_volatility_series(
    symbol: str,
    vol_series: pd.DataFrame,
    output_dir: Path,
) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 6))

    for col in ["rolling_vol_20d", "rolling_vol_60d", "rolling_vol_120d"]:
        if col in vol_series.columns:
            ax.plot(vol_series.index, vol_series[col], label=col)

    ewma_cols = [c for c in vol_series.columns if c.startswith("ewma_vol_lambda_")]
    for col in ewma_cols:
        ax.plot(vol_series.index, vol_series[col], label=col, linewidth=2.0)

    ax.set_title(f"{symbol} Volatility Measures Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Annualized Volatility")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()

    path = output_dir / f"{symbol}_volatility_series.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def plot_event_volatility_comparison(
    symbol: str,
    event_df: pd.DataFrame,
    output_dir: Path,
) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plot_df = event_df.copy()
    plot_df["label"] = plot_df["event_name"] + " " + plot_df["event_date"].dt.strftime("%Y-%m-%d")
    plot_df = plot_df.sort_values("event_date")

    x = range(len(plot_df))
    width = 0.36

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar([i - width / 2 for i in x], plot_df["pre_realized_vol"], width=width, label="Pre-event")
    ax.bar([i + width / 2 for i in x], plot_df["post_realized_vol"], width=width, label="Post-event")

    ax.set_title(f"{symbol} Realized Volatility Around Macro Events")
    ax.set_ylabel("Annualized Realized Volatility")
    ax.set_xticks(list(x))
    ax.set_xticklabels(plot_df["label"], rotation=45, ha="right")
    ax.grid(axis="y", alpha=0.3)
    ax.legend()
    fig.tight_layout()

    path = output_dir / f"{symbol}_event_volatility.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def generate_markdown_report(
    symbol: str,
    summary_df: pd.DataFrame,
    event_df: pd.DataFrame,
    output_dir: Path,
    vol_plot_path: Path | None = None,
    event_plot_path: Path | None = None,
) -> Path:
    row = summary_df.iloc[0].to_dict()

    avg_pre = event_df["pre_realized_vol"].mean() if "pre_realized_vol" in event_df else float("nan")
    avg_post = event_df["post_realized_vol"].mean() if "post_realized_vol" in event_df else float("nan")
    delta = avg_post - avg_pre if pd.notna(avg_pre) and pd.notna(avg_post) else float("nan")
    ratio = (avg_post / avg_pre) if pd.notna(avg_pre) and avg_pre > 0 else float("nan")

    report_lines = [
        f"# {symbol} Volatility Report",
        "",
        "## Snapshot",
        f"- Historical vol: {_format_pct(row.get('historical_vol', float('nan')))}",
        f"- Rolling 20d (latest): {_format_pct(row.get('rolling_20d_latest', float('nan')))}",
        f"- Rolling 60d (latest): {_format_pct(row.get('rolling_60d_latest', float('nan')))}",
        f"- Rolling 120d (latest): {_format_pct(row.get('rolling_120d_latest', float('nan')))}",
        f"- EWMA (latest): {_format_pct(row.get('ewma_latest', float('nan')))}",
        "",
        "## Event Dynamics",
        f"- Average pre-event realized vol: {_format_pct(avg_pre)}",
        f"- Average post-event realized vol: {_format_pct(avg_post)}",
        f"- Average change (post - pre): {_format_pct(delta)}",
        f"- Average ratio (post / pre): {ratio:.3f}" if pd.notna(ratio) else "- Average ratio (post / pre): NA",
        f"- Largest vol increase event: {_top_event_line(event_df, 'vol_change', largest=True)}",
        f"- Largest vol decrease event: {_top_event_line(event_df, 'vol_change', largest=False)}",
        "",
        "## Plots",
        f"- Volatility series plot: `{vol_plot_path.name}`" if vol_plot_path else "- Volatility series plot: not generated",
        f"- Event comparison plot: `{event_plot_path.name}`" if event_plot_path else "- Event comparison plot: not generated",
        "",
        "## Interpretation",
        "Volatility behaves as a dynamic risk metric: rolling and EWMA measures capture regime changes over time,",
        "while pre/post-event realized volatility highlights how macro catalysts can alter short-horizon risk.",
    ]

    report_path = output_dir / f"{symbol}_volatility_report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    return report_path


def build_report(
    symbol: str,
    summary_df: pd.DataFrame,
    vol_series: pd.DataFrame,
    event_df: pd.DataFrame,
    output_dir: Path,
) -> dict[str, Path | None]:
    output_dir.mkdir(parents=True, exist_ok=True)
    vol_plot = plot_volatility_series(symbol=symbol, vol_series=vol_series, output_dir=output_dir)
    event_plot = plot_event_volatility_comparison(symbol=symbol, event_df=event_df, output_dir=output_dir)
    report = generate_markdown_report(
        symbol=symbol,
        summary_df=summary_df,
        event_df=event_df,
        output_dir=output_dir,
        vol_plot_path=vol_plot,
        event_plot_path=event_plot,
    )
    return {"vol_plot": vol_plot, "event_plot": event_plot, "report": report}
