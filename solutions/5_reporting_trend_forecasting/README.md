# Reporting Trend Forecasting

Forecasts monthly adverse event report volumes by FDA product category using time-series models on CAERS data (2004–2017 Q2).

## Methods

| Model | Description | Strengths |
|---|---|---|
| **Prophet** | Additive/multiplicative decomposition with yearly seasonality and automatic changepoint detection | Handles trend shifts and missing data gracefully |
| **ARIMA(2,1,2)** | Classical autoregressive integrated moving average | Good baseline; captures short-term autocorrelation |

Both models are trained on all but the last 6 months, which are held out for evaluation. Forecasts extend 12 months beyond the dataset.

## Usage

```bash
cd solutions/5_reporting_trend_forecasting
pip install pandas numpy matplotlib statsmodels prophet
python main.py
```

## Outputs

| File | Description |
|---|---|
| `overall_trend.png` | Monthly report volumes for the top 6 industries |
| `forecast_<industry>.png` | Side-by-side Prophet vs ARIMA forecast plots per industry |
| `model_comparison.png` | Bar chart comparing MAPE across industries and models |
| `forecast_metrics.csv` | MAE, RMSE, and MAPE for each industry × model combination |
| `future_forecasts.csv` | Prophet forecasts for 12 months beyond the dataset |

## Configuration

Key parameters in `main.py`:

- `TOP_N_INDUSTRIES = 6` — number of industries to forecast
- `FORECAST_MONTHS = 12` — months to forecast beyond dataset
- `TRAIN_CUTOFF_MONTHS = 6` — holdout window for evaluation
- `ARIMA_ORDER = (2, 1, 2)` — ARIMA (p, d, q) order

## Caveats

- Only ~13 years of monthly data — limits long-horizon forecasts
- Exogenous factors (regulation changes, recalls, media coverage) cause structural breaks not captured by these univariate models
- The strong upward trend in reporting likely reflects improved reporting infrastructure, not a proportional increase in actual adverse events
- Prophet's multiplicative seasonality may overfit the late-period spike
