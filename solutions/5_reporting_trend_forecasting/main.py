"""
Reporting Trend Forecasting
============================
Forecasts monthly adverse event report volumes by product category
using Prophet and ARIMA time-series models on FDA CAERS data.
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from prophet import Prophet

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

RANDOM_SEED = 42
TOP_N_INDUSTRIES = 6
FORECAST_MONTHS = 12
ARIMA_ORDER = (2, 1, 2)
TRAIN_CUTOFF_MONTHS = 6  # hold out last N months for evaluation

OUTPUT_DIR = Path(__file__).resolve().parent
DATA_PATH = OUTPUT_DIR / "../../CAERS_ASCII_2004_2017Q2.csv"


# ---------------------------------------------------------------------------
# Data Loading & Preprocessing
# ---------------------------------------------------------------------------

def load_data(path: str | Path) -> pd.DataFrame:
    """Load the CAERS CSV and parse the report creation date."""
    print(f"Loading data from {path}")
    df = pd.read_csv(
        path,
        parse_dates=["RA_CAERS Created Date"],
        date_format="%m/%d/%Y",
    )
    df = df.dropna(subset=["RA_CAERS Created Date", "PRI_FDA Industry Name"])
    df = df.rename(columns=lambda c: c.strip())
    print(f"  {len(df):,} rows with valid date and industry")
    return df


def aggregate_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate report counts into monthly bins per industry."""
    df = df.copy()
    df["month"] = df["RA_CAERS Created Date"].dt.to_period("M").dt.to_timestamp()
    monthly = (
        df.groupby(["month", "PRI_FDA Industry Name"])
        .size()
        .reset_index(name="report_count")
    )
    return monthly


def get_top_industries(df: pd.DataFrame, n: int = TOP_N_INDUSTRIES) -> list[str]:
    """Return the top-N industries by total report volume."""
    return (
        df["PRI_FDA Industry Name"]
        .value_counts()
        .head(n)
        .index.tolist()
    )


def prepare_industry_series(
    monthly: pd.DataFrame, industry: str
) -> pd.DataFrame:
    """
    Extract a complete monthly time series for one industry,
    filling gaps with zero counts.
    """
    ind = monthly[monthly["PRI_FDA Industry Name"] == industry][["month", "report_count"]]
    ind = ind.set_index("month").sort_index()

    # Fill missing months with 0
    full_range = pd.date_range(ind.index.min(), ind.index.max(), freq="MS")
    ind = ind.reindex(full_range, fill_value=0)
    ind.index.name = "month"
    ind = ind.reset_index()
    return ind


# ---------------------------------------------------------------------------
# Train / Test Split
# ---------------------------------------------------------------------------

def split_train_test(
    series: pd.DataFrame, holdout_months: int = TRAIN_CUTOFF_MONTHS
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Hold out the last `holdout_months` for evaluation."""
    cutoff = series["month"].max() - pd.DateOffset(months=holdout_months - 1)
    train = series[series["month"] < cutoff].copy()
    test = series[series["month"] >= cutoff].copy()
    return train, test


# ---------------------------------------------------------------------------
# Prophet Forecasting
# ---------------------------------------------------------------------------

def fit_prophet(
    train: pd.DataFrame,
    periods: int,
    freq: str = "MS",
) -> tuple[Prophet, pd.DataFrame]:
    """Fit a Prophet model and produce a forecast."""
    prophet_df = train.rename(columns={"month": "ds", "report_count": "y"})

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        changepoint_prior_scale=0.1,
        seasonality_mode="multiplicative",
    )
    model.fit(prophet_df)

    future = model.make_future_dataframe(periods=periods, freq=freq)
    forecast = model.predict(future)
    return model, forecast


# ---------------------------------------------------------------------------
# ARIMA Forecasting
# ---------------------------------------------------------------------------

def fit_arima(
    train: pd.DataFrame,
    order: tuple = ARIMA_ORDER,
    forecast_steps: int = FORECAST_MONTHS,
) -> tuple[pd.DataFrame, object]:
    """Fit an ARIMA model and return forecast DataFrame."""
    ts = train.set_index("month")["report_count"].asfreq("MS", fill_value=0)

    model = ARIMA(ts, order=order)
    fitted = model.fit()

    fc = fitted.get_forecast(steps=forecast_steps)
    fc_df = fc.summary_frame(alpha=0.05)
    fc_df.index.name = "month"
    fc_df = fc_df.reset_index()
    return fc_df, fitted


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def compute_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
    """Compute MAE, RMSE, and MAPE for forecast evaluation."""
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    mae = np.mean(np.abs(actual - predicted))
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
    # Avoid divide-by-zero in MAPE
    nonzero = actual != 0
    if nonzero.any():
        mape = np.mean(np.abs((actual[nonzero] - predicted[nonzero]) / actual[nonzero])) * 100
    else:
        mape = np.nan

    return {"MAE": round(mae, 2), "RMSE": round(rmse, 2), "MAPE_%": round(mape, 2)}


# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------

def plot_overall_trend(monthly: pd.DataFrame, top_industries: list[str]):
    """Plot monthly report volumes for top industries."""
    fig, ax = plt.subplots(figsize=(14, 6))

    for industry in top_industries:
        ind = monthly[monthly["PRI_FDA Industry Name"] == industry]
        ax.plot(ind["month"], ind["report_count"], label=industry, linewidth=1.2)

    ax.set_title("Monthly Adverse Event Reports by Industry", fontsize=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("Reports per Month")
    ax.legend(fontsize=8, loc="upper left")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    plt.xticks(rotation=45)
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "overall_trend.png", dpi=150)
    plt.close(fig)
    print("Saved overall_trend.png")


def plot_forecast_comparison(
    industry: str,
    train: pd.DataFrame,
    test: pd.DataFrame,
    prophet_fc: pd.DataFrame,
    arima_fc: pd.DataFrame,
):
    """Plot actual vs forecast for both models on a single industry."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 5), sharey=True)
    safe_name = industry.replace("/", "_").replace(" ", "_")[:40]

    # --- Prophet ---
    ax = axes[0]
    ax.plot(train["month"], train["report_count"], "k-", linewidth=1, label="Train")
    ax.plot(test["month"], test["report_count"], "b-", linewidth=1.5, label="Actual (test)")
    fc_test = prophet_fc[prophet_fc["ds"] >= test["month"].min()]
    ax.plot(fc_test["ds"], fc_test["yhat"], "r--", linewidth=1.5, label="Prophet forecast")
    ax.fill_between(
        fc_test["ds"], fc_test["yhat_lower"], fc_test["yhat_upper"],
        alpha=0.15, color="red",
    )
    ax.set_title(f"Prophet — {industry}", fontsize=10)
    ax.set_xlabel("Date")
    ax.set_ylabel("Reports / month")
    ax.legend(fontsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # --- ARIMA ---
    ax = axes[1]
    ax.plot(train["month"], train["report_count"], "k-", linewidth=1, label="Train")
    ax.plot(test["month"], test["report_count"], "b-", linewidth=1.5, label="Actual (test)")
    ax.plot(arima_fc["month"], arima_fc["mean"], "g--", linewidth=1.5, label="ARIMA forecast")
    ax.fill_between(
        arima_fc["month"], arima_fc["mean_ci_lower"], arima_fc["mean_ci_upper"],
        alpha=0.15, color="green",
    )
    ax.set_title(f"ARIMA{ARIMA_ORDER} — {industry}", fontsize=10)
    ax.set_xlabel("Date")
    ax.legend(fontsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / f"forecast_{safe_name}.png", dpi=150)
    plt.close(fig)
    print(f"  Saved forecast_{safe_name}.png")


def plot_metric_comparison(metrics_df: pd.DataFrame):
    """Bar chart comparing Prophet vs ARIMA MAPE across industries."""
    fig, ax = plt.subplots(figsize=(10, 5))

    industries = metrics_df["industry"].unique()
    x = np.arange(len(industries))
    width = 0.35

    prophet_mape = metrics_df[metrics_df["model"] == "Prophet"]["MAPE_%"].values
    arima_mape = metrics_df[metrics_df["model"] == "ARIMA"]["MAPE_%"].values

    ax.bar(x - width / 2, prophet_mape, width, label="Prophet", color="#d62728")
    ax.bar(x + width / 2, arima_mape, width, label="ARIMA", color="#2ca02c")

    ax.set_ylabel("MAPE (%)")
    ax.set_title("Forecast Accuracy by Industry (lower is better)")
    ax.set_xticks(x)
    ax.set_xticklabels(industries, rotation=30, ha="right", fontsize=8)
    ax.legend()
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "model_comparison.png", dpi=150)
    plt.close(fig)
    print("Saved model_comparison.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Reporting Trend Forecasting")
    print("=" * 60)

    # Load & aggregate
    df = load_data(DATA_PATH)
    monthly = aggregate_monthly(df)
    top_industries = get_top_industries(df, TOP_N_INDUSTRIES)
    print(f"\nTop {TOP_N_INDUSTRIES} industries by report volume:")
    for i, name in enumerate(top_industries, 1):
        print(f"  {i}. {name}")

    # Overall trend plot
    plot_overall_trend(monthly, top_industries)

    # Forecast each industry
    all_metrics = []
    all_forecasts = []

    for industry in top_industries:
        print(f"\n{'─' * 60}")
        print(f"Forecasting: {industry}")
        print(f"{'─' * 60}")

        series = prepare_industry_series(monthly, industry)
        train, test = split_train_test(series, TRAIN_CUTOFF_MONTHS)
        print(f"  Train: {train['month'].min().date()} → {train['month'].max().date()} ({len(train)} months)")
        print(f"  Test:  {test['month'].min().date()} → {test['month'].max().date()} ({len(test)} months)")

        forecast_steps = len(test) + FORECAST_MONTHS

        # --- Prophet ---
        try:
            prophet_model, prophet_fc = fit_prophet(train, periods=forecast_steps)
            # Evaluate on test set
            prophet_test = prophet_fc[prophet_fc["ds"].isin(test["month"])]
            if len(prophet_test) == len(test):
                prophet_metrics = compute_metrics(
                    test["report_count"].values,
                    prophet_test["yhat"].values,
                )
            else:
                prophet_metrics = {"MAE": np.nan, "RMSE": np.nan, "MAPE_%": np.nan}
            print(f"  Prophet — MAE: {prophet_metrics['MAE']}, RMSE: {prophet_metrics['RMSE']}, MAPE: {prophet_metrics['MAPE_%']}%")
        except Exception as e:
            print(f"  Prophet failed: {e}")
            prophet_fc = pd.DataFrame(columns=["ds", "yhat", "yhat_lower", "yhat_upper"])
            prophet_metrics = {"MAE": np.nan, "RMSE": np.nan, "MAPE_%": np.nan}

        # --- ARIMA ---
        try:
            arima_fc, arima_fitted = fit_arima(train, ARIMA_ORDER, forecast_steps)
            # Evaluate on test set
            arima_test = arima_fc.head(len(test))
            arima_metrics = compute_metrics(
                test["report_count"].values,
                arima_test["mean"].values,
            )
            print(f"  ARIMA  — MAE: {arima_metrics['MAE']}, RMSE: {arima_metrics['RMSE']}, MAPE: {arima_metrics['MAPE_%']}%")
        except Exception as e:
            print(f"  ARIMA failed: {e}")
            arima_fc = pd.DataFrame(columns=["month", "mean", "mean_ci_lower", "mean_ci_upper"])
            arima_metrics = {"MAE": np.nan, "RMSE": np.nan, "MAPE_%": np.nan}

        # Record metrics
        all_metrics.append({"industry": industry, "model": "Prophet", **prophet_metrics})
        all_metrics.append({"industry": industry, "model": "ARIMA", **arima_metrics})

        # Record future forecasts (beyond test period) from Prophet
        if len(prophet_fc) > 0:
            future_fc = prophet_fc[prophet_fc["ds"] > series["month"].max()].copy()
            future_fc["industry"] = industry
            future_fc["model"] = "Prophet"
            future_fc = future_fc.rename(columns={"ds": "month", "yhat": "forecast", "yhat_lower": "lower", "yhat_upper": "upper"})
            all_forecasts.append(future_fc[["month", "industry", "model", "forecast", "lower", "upper"]])

        # Plot
        if len(prophet_fc) > 0 and len(arima_fc) > 0:
            plot_forecast_comparison(industry, train, test, prophet_fc, arima_fc)

    # Summary outputs
    metrics_df = pd.DataFrame(all_metrics)
    metrics_df.to_csv(OUTPUT_DIR / "forecast_metrics.csv", index=False)
    print(f"\nSaved forecast_metrics.csv")

    if all_forecasts:
        forecasts_df = pd.concat(all_forecasts, ignore_index=True)
        forecasts_df.to_csv(OUTPUT_DIR / "future_forecasts.csv", index=False)
        print(f"Saved future_forecasts.csv ({len(forecasts_df)} rows)")

    # Model comparison chart
    if not metrics_df["MAPE_%"].isna().all():
        plot_metric_comparison(metrics_df)

    # Print summary table
    print(f"\n{'=' * 60}")
    print("Forecast Accuracy Summary")
    print(f"{'=' * 60}")
    pivot = metrics_df.pivot(index="industry", columns="model", values="MAPE_%")
    print(pivot.to_string())
    print()

    best = metrics_df.loc[metrics_df.groupby("industry")["MAPE_%"].idxmin()]
    for _, row in best.iterrows():
        print(f"  {row['industry'][:40]:40s} → best: {row['model']} (MAPE {row['MAPE_%']:.1f}%)")


if __name__ == "__main__":
    main()
