"""
Serious Outcome Prediction from FDA CAERS Adverse Event Reports
===============================================================
Predicts whether an adverse event report involves serious outcomes
(hospitalization, death, or life-threatening) using XGBoost and
Logistic Regression.
"""

import json
import os
import pickle
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    classification_report,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from scipy.sparse import hstack
from xgboost import XGBClassifier

warnings.filterwarnings("ignore", category=FutureWarning)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, "../../CAERS_ASCII_2004_2017Q2.csv")

AGE_TO_YEARS = {
    "Year(s)": 1.0,
    "Month(s)": 1.0 / 12,
    "Week(s)": 1.0 / 52,
    "Day(s)": 1.0 / 365,
    "Decade(s)": 10.0,
    "Not Available": np.nan,
}
MAX_PLAUSIBLE_AGE = 120


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data(path: str) -> pd.DataFrame:
    print(f"Loading data from {path}")
    df = pd.read_csv(path)
    print(f"  Loaded {len(df):,} rows, {len(df.columns)} columns")
    return df


# ---------------------------------------------------------------------------
# Target engineering
# ---------------------------------------------------------------------------

def create_targets(df: pd.DataFrame) -> pd.DataFrame:
    outcomes = df["AEC_One Row Outcomes"].fillna("")
    df = df.copy()
    df["is_hospitalized"] = outcomes.str.contains("HOSPITALIZATION", case=False).astype(int)
    df["is_death"] = outcomes.str.contains("DEATH", case=False).astype(int)
    df["is_life_threatening"] = outcomes.str.contains("LIFE THREATENING", case=False).astype(int)
    df["is_serious"] = (
        (df["is_hospitalized"] | df["is_death"] | df["is_life_threatening"])
    ).astype(int)

    print("\nTarget distribution:")
    for col in ["is_hospitalized", "is_death", "is_life_threatening", "is_serious"]:
        print(f"  {col}: {df[col].sum():,} ({df[col].mean():.1%})")
    return df


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

def normalize_age(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    raw_age = pd.to_numeric(df["CI_Age at Adverse Event"], errors="coerce")
    unit = df["CI_Age Unit"].map(AGE_TO_YEARS)
    age_years = raw_age * unit

    # Flag impossible ages
    df["age_implausible"] = (age_years > MAX_PLAUSIBLE_AGE).astype(int)
    age_years[age_years > MAX_PLAUSIBLE_AGE] = np.nan

    df["age_missing"] = age_years.isna().astype(int)
    median_age = age_years.median()
    df["age_years"] = age_years.fillna(median_age)

    print(f"\nAge processing:")
    print(f"  Median age (years): {median_age:.1f}")
    print(f"  Missing: {df['age_missing'].sum():,}")
    print(f"  Implausible (>{MAX_PLAUSIBLE_AGE}): {df['age_implausible'].sum():,}")
    return df


def encode_gender(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    gender = df["CI_Gender"].fillna("Not Available")
    df["gender_female"] = (gender == "Female").astype(int)
    df["gender_male"] = (gender == "Male").astype(int)
    df["gender_unknown"] = (~gender.isin(["Female", "Male"])).astype(int)
    return df


def build_symptom_tfidf(texts: pd.Series, max_features: int = 500) -> tuple:
    docs = texts.fillna("").str.replace(",", " ", regex=False)
    vectorizer = TfidfVectorizer(max_features=max_features, token_pattern=r"(?u)\b\w[\w\-]+\b")
    matrix = vectorizer.fit_transform(docs)
    feature_names = [f"tfidf_{t}" for t in vectorizer.get_feature_names_out()]
    print(f"\nTF-IDF symptoms: {matrix.shape[1]} features from {len(docs):,} documents")
    return matrix, feature_names, vectorizer


def encode_industry(df: pd.DataFrame, max_categories: int = 30) -> tuple:
    col = df["PRI_FDA Industry Name"].fillna("Unknown")
    top = col.value_counts().head(max_categories).index.tolist()
    col_clipped = col.where(col.isin(top), other="Other")
    enc = OneHotEncoder(sparse_output=True, handle_unknown="ignore")
    matrix = enc.fit_transform(col_clipped.values.reshape(-1, 1))
    feature_names = [f"industry_{c}" for c in enc.get_feature_names_out()]
    print(f"Industry encoding: {matrix.shape[1]} categories")
    return matrix, feature_names, enc


def build_features(df: pd.DataFrame):
    df = normalize_age(df)
    df = encode_gender(df)

    numeric_cols = ["age_years", "age_missing", "age_implausible",
                    "gender_female", "gender_male", "gender_unknown"]
    X_numeric = df[numeric_cols].values

    tfidf_matrix, tfidf_names, tfidf_vec = build_symptom_tfidf(df["SYM_One Row Coded Symptoms"])
    industry_matrix, industry_names, industry_enc = encode_industry(df)

    X = hstack([
        pd.DataFrame(X_numeric).astype(float).values if False else
        np.asarray(X_numeric, dtype=float),
        tfidf_matrix,
        industry_matrix,
    ], format="csr")

    # scipy hstack needs sparse inputs for all — convert numeric to sparse
    from scipy.sparse import csr_matrix
    X = hstack([csr_matrix(X_numeric.astype(float)), tfidf_matrix, industry_matrix], format="csr")

    feature_names = numeric_cols + tfidf_names + industry_names
    print(f"\nFinal feature matrix: {X.shape[0]:,} x {X.shape[1]:,}")

    artifacts = {"tfidf_vec": tfidf_vec, "industry_enc": industry_enc}
    return X, feature_names, artifacts


# ---------------------------------------------------------------------------
# Modelling
# ---------------------------------------------------------------------------

def train_and_evaluate(X_train, X_test, y_train, y_test, feature_names):
    results = {}

    # --- XGBoost ---
    print("\n" + "=" * 60)
    print("XGBoost")
    print("=" * 60)
    xgb = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=(y_train == 0).sum() / max((y_train == 1).sum(), 1),
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    )
    xgb.fit(X_train, y_train)
    y_prob_xgb = xgb.predict_proba(X_test)[:, 1]
    y_pred_xgb = xgb.predict(X_test)

    auc_xgb = roc_auc_score(y_test, y_prob_xgb)
    print(f"\nROC-AUC: {auc_xgb:.4f}")
    print(classification_report(y_test, y_pred_xgb, digits=3))
    results["xgb"] = {"model": xgb, "y_prob": y_prob_xgb, "y_pred": y_pred_xgb, "auc": auc_xgb}

    # --- Logistic Regression ---
    print("=" * 60)
    print("Logistic Regression")
    print("=" * 60)
    lr = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        C=1.0,
        solver="saga",
        random_state=42,
        n_jobs=-1,
    )
    lr.fit(X_train, y_train)
    y_prob_lr = lr.predict_proba(X_test)[:, 1]
    y_pred_lr = lr.predict(X_test)

    auc_lr = roc_auc_score(y_test, y_prob_lr)
    print(f"\nROC-AUC: {auc_lr:.4f}")
    print(classification_report(y_test, y_pred_lr, digits=3))
    results["lr"] = {"model": lr, "y_prob": y_prob_lr, "y_pred": y_pred_lr, "auc": auc_lr}

    return results


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_roc_curves(y_test, results, save_dir):
    fig, ax = plt.subplots(figsize=(7, 6))
    for label, key in [("XGBoost", "xgb"), ("Logistic Regression", "lr")]:
        RocCurveDisplay.from_predictions(
            y_test, results[key]["y_prob"], name=f"{label} (AUC={results[key]['auc']:.3f})", ax=ax,
        )
    ax.set_title("ROC Curve — Serious Outcome Prediction")
    ax.plot([0, 1], [0, 1], "k--", alpha=0.4)
    fig.tight_layout()
    path = os.path.join(save_dir, "roc_curve.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved ROC curve → {path}")


def plot_confusion_matrices(y_test, results, save_dir):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, (label, key) in zip(axes, [("XGBoost", "xgb"), ("Logistic Regression", "lr")]):
        ConfusionMatrixDisplay.from_predictions(y_test, results[key]["y_pred"], ax=ax, cmap="Blues")
        ax.set_title(f"{label} (AUC={results[key]['auc']:.3f})")
    fig.tight_layout()
    path = os.path.join(save_dir, "confusion_matrices.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved confusion matrices → {path}")


def plot_feature_importance(model, feature_names, save_dir, top_n=20):
    importance = model.feature_importances_
    indices = np.argsort(importance)[-top_n:]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(range(len(indices)), importance[indices], align="center")
    ax.set_yticks(range(len(indices)))
    ax.set_yticklabels([feature_names[i] for i in indices])
    ax.set_xlabel("Feature Importance (gain)")
    ax.set_title(f"XGBoost — Top {top_n} Features")
    fig.tight_layout()
    path = os.path.join(save_dir, "feature_importance.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved feature importance → {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    df = load_data(DATA_PATH)
    df = create_targets(df)

    X, feature_names, artifacts = build_features(df)
    y = df["is_serious"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )
    print(f"\nTrain: {X_train.shape[0]:,}  |  Test: {X_test.shape[0]:,}")
    print(f"Train positive rate: {y_train.mean():.1%}  |  Test positive rate: {y_test.mean():.1%}")

    results = train_and_evaluate(X_train, X_test, y_train, y_test, feature_names)

    plot_roc_curves(y_test, results, SCRIPT_DIR)
    plot_confusion_matrices(y_test, results, SCRIPT_DIR)
    plot_feature_importance(results["xgb"]["model"], feature_names, SCRIPT_DIR)

    # --- Save model artifacts for the web API ---
    artifacts_dir = os.path.join(SCRIPT_DIR, "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)

    with open(os.path.join(artifacts_dir, "xgb_model.pkl"), "wb") as f:
        pickle.dump(results["xgb"]["model"], f)
    with open(os.path.join(artifacts_dir, "lr_model.pkl"), "wb") as f:
        pickle.dump(results["lr"]["model"], f)
    with open(os.path.join(artifacts_dir, "tfidf_vectorizer.pkl"), "wb") as f:
        pickle.dump(artifacts["tfidf_vec"], f)
    with open(os.path.join(artifacts_dir, "industry_encoder.pkl"), "wb") as f:
        pickle.dump(artifacts["industry_enc"], f)

    # Save metadata needed for feature engineering at inference time
    median_age = df["age_years"].median() if "age_years" in df.columns else 45.0
    industry_categories = artifacts["industry_enc"].categories_[0].tolist()
    metadata = {
        "feature_names": feature_names,
        "median_age": float(median_age),
        "industry_categories": industry_categories,
        "xgb_auc": float(results["xgb"]["auc"]),
        "lr_auc": float(results["lr"]["auc"]),
    }
    with open(os.path.join(artifacts_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nSaved model artifacts → {artifacts_dir}")
    print("\nDone.")


if __name__ == "__main__":
    main()
