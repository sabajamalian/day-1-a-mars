# Anomaly Detection for Product Safety Signals

Detects unusual spikes in FDA CAERS adverse event reports as an early warning system for product safety issues.

## Methods

| Method | What it detects | Trend-robust? |
|---|---|---|
| **Z-score** | Weeks where report count deviates >2.5σ from a rolling 12-week baseline | Yes — rolling window adapts to local trend |
| **CUSUM** | Sustained shifts in mean reporting rate (changepoint detection) | Partially — detects shifts relative to overall mean |
| **Isolation Forest** | Anomalous weeks in the multi-industry feature space | Yes — learns normal joint distribution |

Signals flagged by 2+ methods are considered high-confidence anomalies.

## Usage

```bash
cd solutions/3_anomaly_detection
python main.py
```

### Requirements

```
pandas numpy scikit-learn matplotlib seaborn
```

## Outputs

| File | Description |
|---|---|
| `detected_anomalies.csv` | All detected anomalies with date, industry, method(s), and severity score |
| `anomalies_<industry>.png` | Time-series plots with anomalies highlighted (top 5 industries) |
| `anomaly_heatmap.png` | Heatmap of anomaly intensity by industry and year |

## Configuration

Key parameters in `main.py`:

- `ROLLING_WINDOW = 12` — weeks for z-score rolling baseline
- `ZSCORE_THRESHOLD = 2.5` — standard deviations to flag
- `CUSUM_DRIFT = 1.0` / `CUSUM_THRESHOLD = 4.0` — CUSUM sensitivity
- `ISO_CONTAMINATION = 0.05` — expected anomaly fraction for Isolation Forest
- `TOP_N_PRODUCTS = 20` — individual products to track
