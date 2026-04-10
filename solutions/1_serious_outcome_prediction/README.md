# Serious Outcome Prediction

Binary classification to predict whether an FDA CAERS adverse event report involves **serious outcomes** (hospitalization, death, or life-threatening).

## Dataset

FDA CAERS (Center for Adverse Event Reporting System) data, 2004–2017 Q2, with 90,786 reports.

## Features

| Group | Description |
|-------|-------------|
| Age | Normalized to years, with missing/implausible indicators |
| Gender | One-hot encoded (Female, Male, Unknown) |
| Symptoms | TF-IDF (top 500 terms) from MedDRA coded symptoms |
| Industry | One-hot encoded FDA industry name (top 30 + Other) |

## Models

- **XGBoost** — gradient-boosted trees with class-weight balancing
- **Logistic Regression** — L2-regularized with balanced class weights

## Usage

```bash
pip install pandas scikit-learn xgboost numpy matplotlib
python main.py
```

## Outputs

| File | Description |
|------|-------------|
| `roc_curve.png` | ROC curves for both models |
| `confusion_matrices.png` | Side-by-side confusion matrices |
| `feature_importance.png` | Top 20 XGBoost features by gain |
