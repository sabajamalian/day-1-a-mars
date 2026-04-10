"""
API server for Serious Outcome Prediction.
Loads trained model artifacts and serves predictions via REST endpoints.
"""

import json
import os
import pickle

import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
from scipy.sparse import csr_matrix, hstack

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(APP_DIR, "../../solutions/1_serious_outcome_prediction/artifacts")

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# Load artifacts at startup
# ---------------------------------------------------------------------------

def load_artifacts():
    with open(os.path.join(ARTIFACTS_DIR, "xgb_model.pkl"), "rb") as f:
        xgb_model = pickle.load(f)
    with open(os.path.join(ARTIFACTS_DIR, "lr_model.pkl"), "rb") as f:
        lr_model = pickle.load(f)
    with open(os.path.join(ARTIFACTS_DIR, "tfidf_vectorizer.pkl"), "rb") as f:
        tfidf_vec = pickle.load(f)
    with open(os.path.join(ARTIFACTS_DIR, "industry_encoder.pkl"), "rb") as f:
        industry_enc = pickle.load(f)
    with open(os.path.join(ARTIFACTS_DIR, "metadata.json"), "r") as f:
        metadata = json.load(f)
    return xgb_model, lr_model, tfidf_vec, industry_enc, metadata


xgb_model, lr_model, tfidf_vec, industry_enc, metadata = load_artifacts()
MEDIAN_AGE = metadata["median_age"]
FEATURE_NAMES = metadata["feature_names"]
INDUSTRY_CATEGORIES = metadata["industry_categories"]

print(f"Loaded models. Feature space: {len(FEATURE_NAMES)} features.")
print(f"XGBoost AUC: {metadata['xgb_auc']:.4f}  |  LR AUC: {metadata['lr_auc']:.4f}")


# ---------------------------------------------------------------------------
# Feature engineering (mirrors main.py logic)
# ---------------------------------------------------------------------------

MAX_PLAUSIBLE_AGE = 120


def build_inference_features(age, gender, symptoms_text, industry_name):
    """Build the same feature vector the model was trained on."""

    # --- Numeric features ---
    age_val = float(age) if age is not None else np.nan

    age_implausible = 1 if (age_val is not None and age_val > MAX_PLAUSIBLE_AGE) else 0
    if age_implausible:
        age_val = np.nan

    age_missing = 1 if np.isnan(age_val) else 0
    age_years = MEDIAN_AGE if np.isnan(age_val) else age_val

    gender = (gender or "").strip().capitalize()
    gender_female = 1 if gender == "Female" else 0
    gender_male = 1 if gender == "Male" else 0
    gender_unknown = 1 if gender not in ("Female", "Male") else 0

    numeric = np.array([[age_years, age_missing, age_implausible,
                          gender_female, gender_male, gender_unknown]], dtype=float)

    # --- TF-IDF symptom features ---
    symptoms_clean = (symptoms_text or "").replace(",", " ")
    tfidf_matrix = tfidf_vec.transform([symptoms_clean])

    # --- Industry one-hot ---
    industry_val = industry_name or "Other"
    # Clip to known categories
    if industry_val not in INDUSTRY_CATEGORIES:
        industry_val = "Other"
    industry_matrix = industry_enc.transform(np.array([[industry_val]]))

    # Combine (same order as training)
    X = hstack([csr_matrix(numeric), tfidf_matrix, industry_matrix], format="csr")
    return X


def get_top_contributing_features(model, X, top_n=8):
    """Get the features with highest contribution to this prediction."""
    # Use the raw feature values weighted by importance
    importances = model.feature_importances_
    # For sparse input, convert the single row to dense
    x_dense = np.asarray(X.todense()).flatten()

    # Contribution = feature_value * feature_importance
    contributions = x_dense * importances
    top_indices = np.argsort(np.abs(contributions))[-top_n:][::-1]

    results = []
    for idx in top_indices:
        if abs(contributions[idx]) > 1e-6:
            results.append({
                "feature": FEATURE_NAMES[idx],
                "contribution": round(float(contributions[idx]), 5),
                "value": round(float(x_dense[idx]), 5),
                "importance": round(float(importances[idx]), 5),
            })
    return results


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.get_json(force=True)

    age = data.get("age")
    gender = data.get("gender", "Unknown")
    symptoms = data.get("symptoms", "")
    industry = data.get("industry", "Other")

    # Validate
    if age is not None:
        try:
            age = float(age)
        except (ValueError, TypeError):
            return jsonify({"error": "age must be a number"}), 400

    if not symptoms or not symptoms.strip():
        return jsonify({"error": "symptoms text is required"}), 400

    X = build_inference_features(age, gender, symptoms, industry)

    # XGBoost prediction
    xgb_prob = float(xgb_model.predict_proba(X)[0, 1])
    xgb_pred = int(xgb_prob >= 0.5)

    # Logistic Regression prediction
    lr_prob = float(lr_model.predict_proba(X)[0, 1])
    lr_pred = int(lr_prob >= 0.5)

    # Feature contributions
    top_features = get_top_contributing_features(xgb_model, X)

    return jsonify({
        "xgboost": {
            "probability": round(xgb_prob, 4),
            "prediction": xgb_pred,
            "label": "Serious" if xgb_pred else "Non-Serious",
        },
        "logistic_regression": {
            "probability": round(lr_prob, 4),
            "prediction": lr_pred,
            "label": "Serious" if lr_pred else "Non-Serious",
        },
        "top_features": top_features,
        "input": {
            "age": age,
            "gender": gender,
            "symptoms": symptoms,
            "industry": industry,
        },
    })


@app.route("/api/metadata", methods=["GET"])
def get_metadata():
    return jsonify({
        "feature_count": len(FEATURE_NAMES),
        "industry_categories": INDUSTRY_CATEGORIES,
        "median_age": MEDIAN_AGE,
        "xgb_auc": metadata["xgb_auc"],
        "lr_auc": metadata["lr_auc"],
    })


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
