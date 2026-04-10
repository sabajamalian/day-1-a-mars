# Model Integration — Flask API Pattern

When a premium UI needs to interact with a trained ML model, create a Flask API backend that serves real predictions. Never approximate model behavior with client-side heuristics.

## Architecture

```
web-ui/<solution-name>/
├── index.html          # Frontend
├── styles.css
├── app.js              # Calls the API
└── api.py              # Flask server — loads model, serves predictions

solutions/<solution-name>/
├── main.py             # Training script (saves artifacts)
└── artifacts/
    ├── model.pkl       # Serialized trained model
    ├── vectorizer.pkl  # Fitted TF-IDF / text vectorizer
    ├── encoder.pkl     # Fitted categorical encoder
    └── metadata.json   # Feature names, categories, metrics
```

## Step 1: Save Artifacts from Training

Modify the training script (`main.py`) to export everything needed for inference. Use `pickle` for sklearn/xgboost objects and JSON for metadata.

```python
import json
import pickle

# After training...
artifacts_dir = os.path.join(SCRIPT_DIR, "artifacts")
os.makedirs(artifacts_dir, exist_ok=True)

# Save model
with open(os.path.join(artifacts_dir, "model.pkl"), "wb") as f:
    pickle.dump(trained_model, f)

# Save fitted preprocessors (critical: must be the same objects used in training)
with open(os.path.join(artifacts_dir, "vectorizer.pkl"), "wb") as f:
    pickle.dump(tfidf_vectorizer, f)
with open(os.path.join(artifacts_dir, "encoder.pkl"), "wb") as f:
    pickle.dump(onehot_encoder, f)

# Save metadata
metadata = {
    "feature_names": feature_names,
    "categories": encoder.categories_[0].tolist(),
    "median_values": {"age": float(median_age)},
    "metrics": {"auc": float(auc_score)},
}
with open(os.path.join(artifacts_dir, "metadata.json"), "w") as f:
    json.dump(metadata, f, indent=2)
```

## Step 2: Build the Flask API

Create `api.py` in the web-ui directory.

### Required structure

```python
import json
import os
import pickle

import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
from scipy.sparse import csr_matrix, hstack

app = Flask(__name__)
CORS(app)  # Required: frontend is served from file:// or different origin

# Load artifacts once at startup — not per-request
ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "../../solutions/<name>/artifacts")
model = pickle.load(open(os.path.join(ARTIFACTS_DIR, "model.pkl"), "rb"))
vectorizer = pickle.load(open(os.path.join(ARTIFACTS_DIR, "vectorizer.pkl"), "rb"))
encoder = pickle.load(open(os.path.join(ARTIFACTS_DIR, "encoder.pkl"), "rb"))
metadata = json.load(open(os.path.join(ARTIFACTS_DIR, "metadata.json")))
```

### Feature engineering must mirror training

This is the most critical requirement. Use the **same fitted transformers** from training, not new ones.

```python
def build_inference_features(raw_input):
    """Replicate the exact feature engineering from main.py."""
    # Numeric features — same normalization, same imputation values
    # Text features — use the SAME fitted vectorizer (not a new one)
    tfidf_matrix = vectorizer.transform([text_input])
    # Categorical features — use the SAME fitted encoder
    cat_matrix = encoder.transform([[category_value]])
    # Combine in the SAME ORDER as training
    X = hstack([csr_matrix(numeric), tfidf_matrix, cat_matrix], format="csr")
    return X
```

### Required endpoints

```python
@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.get_json(force=True)
    # Validate inputs
    # Build features using fitted transformers
    X = build_inference_features(data)
    # Return probabilities, not just labels
    prob = float(model.predict_proba(X)[0, 1])
    return jsonify({
        "probability": round(prob, 4),
        "prediction": int(prob >= 0.5),
        "label": "Positive" if prob >= 0.5 else "Negative",
        "top_features": get_contributing_features(model, X),
    })

@app.route("/api/metadata", methods=["GET"])
def get_metadata():
    return jsonify(metadata)

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})
```

### Run configuration

```python
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
```

Always use a non-standard port (e.g. `5001`) to avoid conflicts.

## Step 3: Wire the Frontend

### API call pattern

```js
const API_BASE = 'http://127.0.0.1:5001';

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  // Show loading state
  submitBtn.disabled = true;
  submitBtn.textContent = 'Running inference…';

  try {
    const response = await fetch(`${API_BASE}/api/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ /* form values */ }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.error || `API error ${response.status}`);
    }

    const result = await response.json();
    // Render real model output
    renderPrediction(result);

  } catch (err) {
    // Show connection error with startup instructions
    showError(err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Run Prediction';
  }
});
```

### Error state is required

When the API is not running, the frontend must show a clear error with the command to start the server:

```js
function showError(message) {
  resultEl.innerHTML = `
    <p class="error-title">API Connection Failed</p>
    <p class="error-detail">
      ${message}<br>
      Make sure the API server is running:<br>
      <code>python3 api.py</code>
    </p>
  `;
}
```

### Populate dropdowns from metadata

If the model uses categorical features, fetch categories from the API at page load rather than hardcoding them:

```js
fetch(`${API_BASE}/api/metadata`)
  .then(r => r.json())
  .then(data => {
    const select = document.getElementById('categorySelect');
    data.categories.forEach(cat => {
      const opt = document.createElement('option');
      opt.value = cat;
      opt.textContent = cat;
      select.appendChild(opt);
    });
  })
  .catch(() => {
    // Fall back to hardcoded defaults if API is not running
  });
```

## Common Mistakes to Avoid

| Mistake | Why It Breaks | Fix |
|---------|--------------|-----|
| Fitting a new vectorizer at inference | Different vocabulary → wrong feature indices | Load the pickled vectorizer from training |
| Combining features in wrong order | Feature matrix columns mismatch the model | Numeric, then TF-IDF, then categorical — same as training |
| Returning only class labels | UI can't show probability ring/gauge | Always use `predict_proba()` |
| Missing CORS | Browser blocks cross-origin fetch | Add `flask-cors` (`CORS(app)`) |
| Loading model per-request | Slow response, high memory | Load once at module level |
| No input validation | Server crashes on bad input | Validate and return 400 with error message |
