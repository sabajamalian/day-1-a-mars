"""
Anomaly Detection for Product Safety Signals
=============================================
Detects unusual spikes in FDA CAERS adverse event reports using
Isolation Forest, CUSUM, and Z-score methods as an early warning
system for product safety signals.
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
import seaborn as sns
from sklearn.ensemble import IsolationForest

warnings.filterwarnings("ignore", category=FutureWarning)

RANDOM_SEED = 42
TOP_N_PRODUCTS = 20
ROLLING_WINDOW = 12  # weeks
ZSCORE_THRESHOLD = 2.5
CUSUM_DRIFT = 1.0  # allowable drift in std units
CUSUM_THRESHOLD = 4.0  # decision interval in std units
ISO_CONTAMINATION = 0.05

OUTPUT_DIR = Path(__file__).resolve().parent
DATA_PATH = OUTPUT_DIR / "../../CAERS_ASCII_2004_2017Q2.csv"


# ---------------------------------------------------------------------------
# Data Loading & Preprocessing
# ---------------------------------------------------------------------------

def load_data(path: str | Path) -> pd.DataFrame:
    """Load the CAERS CSV and parse dates."""
    df = pd.read_csv(
        path,
        parse_dates=["RA_CAERS Created Date"],
        date_format="%m/%d/%Y",
    )
    df = df.dropna(subset=["RA_CAERS Created Date"])
    df = df.rename(columns=lambda c: c.strip())
    return df


def aggregate_weekly_by_industry(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate report counts into weekly bins per industry."""
    df = df.copy()
    df["week"] = df["RA_CAERS Created Date"].dt.to_period("W").dt.start_time
    weekly = (
        df.groupby(["week", "PRI_FDA Industry Name"])
        .size()
        .reset_index(name="report_count")
    )
    return weekly


def aggregate_weekly_by_product(df: pd.DataFrame, top_n: int = TOP_N_PRODUCTS) -> pd.DataFrame:
    """Aggregate weekly counts for top-N individual products (excluding REDACTED)."""
    filtered = df[~df["PRI_Reported Brand/Product Name"].str.upper().str.contains("REDACTED", na=False)]
    top_products = (
        filtered["PRI_Reported Brand/Product Name"]
        .value_counts()
        .head(top_n)
        .index.tolist()
    )
    filtered = filtered[filtered["PRI_Reported Brand/Product Name"].isin(top_products)].copy()
    filtered["week"] = filtered["RA_CAERS Created Date"].dt.to_period("W").dt.start_time
    weekly = (
        filtered.groupby(["week", "PRI_Reported Brand/Product Name"])
        .size()
        .reset_index(name="report_count")
    )
    return weekly, top_products


# ---------------------------------------------------------------------------
# Anomaly Detection Methods
# ---------------------------------------------------------------------------

def detect_zscore_anomalies(
    series: pd.Series,
    window: int = ROLLING_WINDOW,
    threshold: float = ZSCORE_THRESHOLD,
) -> pd.DataFrame:
    """Flag points where z-score vs rolling baseline exceeds threshold."""
    rolling_mean = series.rolling(window=window, min_periods=3).mean().shift(1)
    rolling_std = series.rolling(window=window, min_periods=3).std().shift(1)
    rolling_std = rolling_std.replace(0, np.nan)
    zscore = (series - rolling_mean) / rolling_std
    anomalies = zscore.abs() > threshold
    return pd.DataFrame({
        "report_count": series,
        "rolling_mean": rolling_mean,
        "rolling_std": rolling_std,
        "zscore": zscore,
        "is_anomaly": anomalies,
    })


def detect_cusum_anomalies(
    series: pd.Series,
    drift: float = CUSUM_DRIFT,
    threshold: float = CUSUM_THRESHOLD,
) -> pd.DataFrame:
    """Detect changepoints using tabular CUSUM on standardised residuals."""
    mu = series.mean()
    sigma = series.std()
    if sigma == 0:
        sigma = 1.0
    standardised = (series - mu) / sigma
    s_pos = np.zeros(len(series))
    s_neg = np.zeros(len(series))
    anomalies = np.zeros(len(series), dtype=bool)
    for i in range(1, len(series)):
        s_pos[i] = max(0, s_pos[i - 1] + standardised.iloc[i] - drift)
        s_neg[i] = max(0, s_neg[i - 1] - standardised.iloc[i] - drift)
        if s_pos[i] > threshold or s_neg[i] > threshold:
            anomalies[i] = True
    return pd.DataFrame({
        "report_count": series.values,
        "cusum_pos": s_pos,
        "cusum_neg": s_neg,
        "is_anomaly": anomalies,
    }, index=series.index)


def detect_isolation_forest_anomalies(weekly: pd.DataFrame) -> pd.DataFrame:
    """Run Isolation Forest on pivoted weekly industry counts."""
    pivot = weekly.pivot_table(
        index="week", columns="PRI_FDA Industry Name",
        values="report_count", fill_value=0,
    )
    model = IsolationForest(
        contamination=ISO_CONTAMINATION,
        random_state=RANDOM_SEED,
        n_estimators=200,
    )
    scores = model.fit(pivot).decision_function(pivot)
    labels = model.predict(pivot)
    result = pd.DataFrame({
        "week": pivot.index,
        "iso_score": scores,
        "iso_anomaly": labels == -1,
    })
    return result, pivot


# ---------------------------------------------------------------------------
# Analysis Helpers
# ---------------------------------------------------------------------------

def build_anomaly_table(
    weekly: pd.DataFrame,
    iso_results: pd.DataFrame,
) -> pd.DataFrame:
    """Combine per-industry z-score/CUSUM anomalies with Isolation Forest results."""
    records = []
    industries = weekly["PRI_FDA Industry Name"].unique()
    for industry in industries:
        ind_data = (
            weekly[weekly["PRI_FDA Industry Name"] == industry]
            .sort_values("week")
            .set_index("week")
        )
        if len(ind_data) < 6:
            continue
        zs = detect_zscore_anomalies(ind_data["report_count"])
        cs = detect_cusum_anomalies(ind_data["report_count"])
        for idx in ind_data.index:
            row_z = zs.loc[idx] if idx in zs.index else None
            row_c = cs.loc[idx] if idx in cs.index else None
            iso_row = iso_results[iso_results["week"] == idx]
            methods = []
            severity = 0.0
            if row_z is not None and row_z["is_anomaly"]:
                methods.append("zscore")
                severity = max(severity, abs(row_z["zscore"]))
            if row_c is not None and row_c["is_anomaly"]:
                methods.append("cusum")
                severity = max(severity, max(row_c["cusum_pos"], row_c["cusum_neg"]))
            if not iso_row.empty and iso_row.iloc[0]["iso_anomaly"]:
                methods.append("isolation_forest")
                severity = max(severity, abs(iso_row.iloc[0]["iso_score"]))
            if methods:
                records.append({
                    "week": idx,
                    "industry": industry,
                    "report_count": ind_data.loc[idx, "report_count"],
                    "methods": "+".join(methods),
                    "n_methods": len(methods),
                    "severity_score": round(severity, 3),
                })

    anomalies_df = pd.DataFrame(records)
    if anomalies_df.empty:
        return anomalies_df
    return anomalies_df.sort_values(
        ["n_methods", "severity_score"], ascending=[False, False]
    ).reset_index(drop=True)


def top_industries_by_anomaly_count(anomaly_df: pd.DataFrame, n: int = 5) -> list[str]:
    """Return industries with the most multi-method anomalies."""
    if anomaly_df.empty:
        return []
    counts = (
        anomaly_df[anomaly_df["n_methods"] >= 2]
        .groupby("industry")
        .size()
        .sort_values(ascending=False)
    )
    if counts.empty:
        counts = anomaly_df.groupby("industry").size().sort_values(ascending=False)
    return counts.head(n).index.tolist()


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_industry_timeseries(
    weekly: pd.DataFrame,
    anomaly_df: pd.DataFrame,
    industries: list[str],
    output_dir: Path,
) -> list[Path]:
    """Generate time-series plots with anomalies highlighted for given industries."""
    saved = []
    for industry in industries:
        ind_data = (
            weekly[weekly["PRI_FDA Industry Name"] == industry]
            .sort_values("week")
            .set_index("week")
        )
        if ind_data.empty:
            continue

        ind_anomalies = anomaly_df[anomaly_df["industry"] == industry]

        fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
        fig.suptitle(f"Anomaly Detection — {industry}", fontsize=13, weight="bold")

        # --- Z-score subplot ---
        ax = axes[0]
        zs = detect_zscore_anomalies(ind_data["report_count"])
        ax.plot(ind_data.index, ind_data["report_count"], linewidth=0.8, label="Weekly reports")
        ax.plot(ind_data.index, zs["rolling_mean"], linewidth=0.8, linestyle="--", label="Rolling mean")
        zs_anom = zs[zs["is_anomaly"]]
        ax.scatter(zs_anom.index, zs_anom["report_count"], color="red", s=30, zorder=5, label="Z-score anomaly")
        ax.set_ylabel("Report count")
        ax.set_title("Z-score method", fontsize=10)
        ax.legend(fontsize=8, loc="upper left")

        # --- CUSUM subplot ---
        ax = axes[1]
        cs = detect_cusum_anomalies(ind_data["report_count"])
        ax.plot(ind_data.index, cs["cusum_pos"], linewidth=0.8, label="CUSUM+")
        ax.plot(ind_data.index, cs["cusum_neg"], linewidth=0.8, label="CUSUM−")
        ax.axhline(CUSUM_THRESHOLD, color="red", linestyle="--", linewidth=0.7, label="Threshold")
        cs_anom = cs[cs["is_anomaly"]]
        ax.scatter(cs_anom.index, cs_anom["cusum_pos"], color="red", s=20, zorder=5)
        ax.set_ylabel("CUSUM statistic")
        ax.set_title("CUSUM method", fontsize=10)
        ax.legend(fontsize=8, loc="upper left")

        # --- Combined anomaly subplot ---
        ax = axes[2]
        ax.plot(ind_data.index, ind_data["report_count"], linewidth=0.8, color="steelblue", label="Weekly reports")
        for n_m, color, label in [(3, "red", "3 methods"), (2, "orange", "2 methods"), (1, "gold", "1 method")]:
            subset = ind_anomalies[ind_anomalies["n_methods"] == n_m]
            if subset.empty:
                continue
            merged = subset.merge(ind_data.reset_index(), left_on="week", right_on="week", suffixes=("", "_r"))
            ax.scatter(merged["week"], merged["report_count"], color=color, s=30, zorder=5, label=label)
        ax.set_ylabel("Report count")
        ax.set_title("All methods combined", fontsize=10)
        ax.legend(fontsize=8, loc="upper left")

        for a in axes:
            a.xaxis.set_major_locator(mdates.YearLocator())
            a.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
            a.grid(alpha=0.3)

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        safe_name = industry.replace("/", "_").replace(" ", "_")[:60]
        fpath = output_dir / f"anomalies_{safe_name}.png"
        fig.savefig(fpath, dpi=150)
        plt.close(fig)
        saved.append(fpath)
        print(f"  Saved plot: {fpath.name}")
    return saved


def plot_overview_heatmap(anomaly_df: pd.DataFrame, output_dir: Path) -> Path:
    """Heatmap of anomaly counts per industry per year."""
    if anomaly_df.empty:
        return None
    df = anomaly_df.copy()
    df["year"] = pd.to_datetime(df["week"]).dt.year
    pivot = df.pivot_table(index="industry", columns="year", values="n_methods", aggfunc="sum", fill_value=0)
    top_industries = pivot.sum(axis=1).sort_values(ascending=False).head(15).index
    pivot = pivot.loc[top_industries]
    fig, ax = plt.subplots(figsize=(14, 7))
    sns.heatmap(pivot, annot=True, fmt="g", cmap="YlOrRd", ax=ax, linewidths=0.5)
    ax.set_title("Anomaly Signal Intensity by Industry and Year", fontsize=13, weight="bold")
    ax.set_ylabel("")
    ax.set_xlabel("Year")
    plt.tight_layout()
    fpath = output_dir / "anomaly_heatmap.png"
    fig.savefig(fpath, dpi=150)
    plt.close(fig)
    print(f"  Saved plot: {fpath.name}")
    return fpath


# ---------------------------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------------------------

def main():
    np.random.seed(RANDOM_SEED)
    print("=" * 70)
    print("ANOMALY DETECTION FOR PRODUCT SAFETY SIGNALS")
    print("=" * 70)

    # --- Load ---
    print("\n[1/5] Loading data...")
    df = load_data(DATA_PATH)
    print(f"  Loaded {len(df):,} rows, date range: "
          f"{df['RA_CAERS Created Date'].min():%Y-%m-%d} to "
          f"{df['RA_CAERS Created Date'].max():%Y-%m-%d}")

    # --- Aggregate ---
    print("\n[2/5] Aggregating weekly report counts...")
    weekly_industry = aggregate_weekly_by_industry(df)
    n_industries = weekly_industry["PRI_FDA Industry Name"].nunique()
    n_weeks = weekly_industry["week"].nunique()
    print(f"  {n_industries} industries, {n_weeks} weeks")

    weekly_product, top_products = aggregate_weekly_by_product(df)
    print(f"  Top {len(top_products)} products tracked individually")

    # --- Isolation Forest ---
    print("\n[3/5] Running anomaly detection...")
    print("  - Isolation Forest on industry-week matrix...")
    iso_results, pivot_matrix = detect_isolation_forest_anomalies(weekly_industry)
    iso_count = iso_results["iso_anomaly"].sum()
    print(f"    {iso_count} anomalous weeks flagged ({iso_count/len(iso_results)*100:.1f}%)")

    # --- Build combined anomaly table ---
    print("  - Z-score and CUSUM per industry...")
    anomaly_df = build_anomaly_table(weekly_industry, iso_results)
    print(f"    {len(anomaly_df):,} total anomaly signals detected")

    multi = anomaly_df[anomaly_df["n_methods"] >= 2] if not anomaly_df.empty else anomaly_df
    print(f"    {len(multi):,} confirmed by 2+ methods (high confidence)")

    # --- Save anomaly CSV ---
    print("\n[4/5] Saving outputs...")
    csv_path = OUTPUT_DIR / "detected_anomalies.csv"
    anomaly_df.to_csv(csv_path, index=False)
    print(f"  Saved: {csv_path.name} ({len(anomaly_df)} rows)")

    # --- Plots ---
    print("\n[5/5] Generating plots...")
    top_ind = top_industries_by_anomaly_count(anomaly_df, n=5)
    print(f"  Plotting top industries: {top_ind}")
    plot_industry_timeseries(weekly_industry, anomaly_df, top_ind, OUTPUT_DIR)
    plot_overview_heatmap(anomaly_df, OUTPUT_DIR)

    # --- Summary ---
    print("\n" + "=" * 70)
    print("ANOMALY SUMMARY")
    print("=" * 70)
    if anomaly_df.empty:
        print("  No anomalies detected.")
        return

    print(f"\nTotal anomaly signals:  {len(anomaly_df):,}")
    print(f"High-confidence (2+ methods): {len(multi):,}")
    print(f"\nTop 10 anomalies by severity:\n")
    top10 = anomaly_df.head(10)[["week", "industry", "report_count", "methods", "severity_score"]]
    print(top10.to_string(index=False))

    print(f"\nAnomalies by method:")
    for method in ["zscore", "cusum", "isolation_forest"]:
        count = anomaly_df["methods"].str.contains(method).sum()
        print(f"  {method:20s}: {count:,}")

    print(f"\nTop industries by anomaly frequency:")
    freq = anomaly_df.groupby("industry").size().sort_values(ascending=False).head(10)
    for ind, cnt in freq.items():
        print(f"  {ind:40s}: {cnt:,} signals")

    print(f"\nOutputs saved to: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
