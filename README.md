# Volatility Estimator Project

This project compares multiple volatility measures for the same asset and treats volatility as a dynamic risk metric.

Implemented features:
- Historical volatility from log returns
- Rolling annualized volatility using 20, 60, and 120-day windows
- EWMA volatility to react faster to recent shocks
- Realized-volatility comparison before vs after macro events (e.g., CPI, central bank meetings)
- Auto-generated plots and markdown report

## Project Structure

```
volatility_estimator/
  data/
    macro_events_sample.csv
  src/volatility_estimator/
    cli.py
    data_loader.py
    events.py
    volatility.py
  tests/
    test_volatility.py
  pyproject.toml
  README.md
```

## Install

```bash
cd /Users/indumathi/Documents/Playground/volatility_estimator
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Optional market-data source:

```bash
pip install -e .[dev,market]
```

## Input Formats

### Prices CSV

Must contain:
- `Date`
- `Close`

Example:

```csv
Date,Close
2024-01-02,472.34
2024-01-03,469.11
```

### Macro Events CSV

Must contain:
- `event_date`
- `event_name`

Use `data/macro_events_sample.csv` as a template.

## Run

### 1) Using a local CSV

```bash
vol-estimator \
  --symbol SPY \
  --source csv \
  --prices-csv /absolute/path/to/spy_prices.csv \
  --events-csv data/macro_events_sample.csv \
  --event-window-days 10 \
  --ewma-lambda 0.94 \
  --output-dir outputs
```

### 2) Using yfinance

```bash
vol-estimator \
  --symbol SPY \
  --source yfinance \
  --start 2022-01-01 \
  --events-csv data/macro_events_sample.csv \
  --event-window-days 10 \
  --ewma-lambda 0.94 \
  --output-dir outputs
```

## Outputs

Generated in `outputs/`:
- `<SYMBOL>_vol_summary.csv`: latest snapshot of historical, rolling, and EWMA vol
- `<SYMBOL>_vol_series.csv`: time series of rolling and EWMA volatility
- `<SYMBOL>_event_vol_comparison.csv`: pre/post realized vol around each event
- `<SYMBOL>_volatility_series.png`: rolling + EWMA volatility chart
- `<SYMBOL>_event_volatility.png`: pre vs post event realized volatility bars
- `<SYMBOL>_volatility_report.md`: auto summary report with interpretation

To skip plots/report:

```bash
vol-estimator ... --skip-report
```

## Why this matters

The event-window analysis shows volatility is not static. It shifts around macro catalysts, which is useful for:
- risk budgeting
- tactical position sizing
- scenario-aware portfolio monitoring
# volatility_estimator
