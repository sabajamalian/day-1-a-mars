---
applyTo: "**/*.py"
description: "Use when writing or modifying Python files. Enforces data science coding standards, consistent style, and best practices for ML pipelines, feature engineering, and data processing."
---

# Python Data Science Standards

## Module Structure

Organize every Python module in this order:

1. Module docstring (one-liner describing purpose)
2. `from __future__ import annotations`
3. Standard library imports
4. Third-party imports
5. Local imports
6. Module-level constants (UPPER_SNAKE_CASE)
7. Function/class definitions
8. `if __name__ == "__main__":` guard (for scripts)

## Constants & Configuration

- Define all hyperparameters, thresholds, and magic numbers as module-level constants at the top of the file.
- Use UPPER_SNAKE_CASE for constants: `RANDOM_SEED = 42`, `TEST_SIZE = 0.2`.
- Never bury configuration values inside function bodies or default arguments.
- Use a single `RANDOM_SEED` constant and pass it to every stochastic operation.

## Type Hints

- Annotate all function parameters and return types.
- Use `pd.DataFrame`, `pd.Series`, `np.ndarray`, `scipy.sparse.spmatrix` for data types.
- Use `Path | str` for file path parameters.

```python
def load_data(path: Path | str) -> pd.DataFrame:
```

## Docstrings

- Every function must have a docstring.
- Use a single-line summary for simple functions.
- For complex functions, include Args/Returns/Raises sections:

```python
def train_model(X: spmatrix, y: np.ndarray) -> XGBClassifier:
    """Train an XGBoost classifier on sparse feature matrix.

    Args:
        X: Sparse feature matrix (TF-IDF + encoded categoricals).
        y: Binary target array.

    Returns:
        Fitted XGBClassifier instance.
    """
```

## Path Handling

- Use `pathlib.Path` for all file system operations. Do not use `os.path`.
- Resolve script-relative paths with `Path(__file__).resolve().parent`.
- Define path constants at module level:

```python
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_PATH = SCRIPT_DIR.parent.parent / "CAERS_ASCII_2004_2017Q2.csv"
OUTPUT_DIR = SCRIPT_DIR / "artifacts"
```

## Data Loading & Validation

- Wrap `pd.read_csv()` calls with explicit `encoding` and `parse_dates` parameters when needed.
- Validate loaded data immediately after loading: check shape, required columns, and non-empty DataFrame.
- Log row counts after filtering or dropping nulls.

```python
df = pd.read_csv(DATA_PATH, encoding="latin-1")
assert not df.empty, f"No data loaded from {DATA_PATH}"
assert all(col in df.columns for col in REQUIRED_COLUMNS), "Missing required columns"
```

## Logging

- Use the `logging` module, not `print()`.
- Configure a module-level logger: `logger = logging.getLogger(__name__)`.
- Use appropriate levels: `info` for progress milestones, `warning` for data quality issues, `debug` for detail.
- Configure logging format in `main()`:

```python
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
```

## ML Pipeline Conventions

- Set `random_state=RANDOM_SEED` on every estimator, splitter, and sampler.
- Use stratified splits for classification tasks.
- Log dataset shape after each transformation step.
- Save trained models with `joblib.dump()`, not `pickle.dump()`. Joblib handles large numpy arrays and sparse matrices more efficiently.
- Save model metadata (feature names, training metrics, class distributions) as a sidecar JSON file alongside the model artifact.

## Feature Engineering

- Keep feature engineering in dedicated functions, separate from model training.
- Return sparse matrices (`scipy.sparse.csr_matrix`) for high-dimensional text/categorical features.
- Document the expected input and output shapes in the docstring.

## Error Handling

- Wrap model fitting in try/except to catch convergence or data issues, and log the error before re-raising.
- Validate inputs at function boundaries (public functions), not deep inside helper logic.

## Output & Artifacts

- Create output directories with `OUTPUT_DIR.mkdir(parents=True, exist_ok=True)`.
- Save plots with `plt.savefig()` using `dpi=150, bbox_inches="tight"` then call `plt.close()`.
- Save DataFrames as CSV with `index=False` unless the index carries meaning.
