"""
Symptom Clustering / Syndrome Identification
=============================================
Discovers latent clusters of co-occurring adverse-event symptoms in the
FDA CAERS dataset using UMAP dimensionality reduction and HDBSCAN clustering.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.sparse import csr_matrix
from umap import UMAP
from hdbscan import HDBSCAN

RANDOM_SEED = 42
MIN_SYMPTOM_REPORTS = 50
MIN_CLUSTER_SIZE = 100
UMAP_N_COMPONENTS_VIZ = 2
UMAP_N_COMPONENTS_CLUSTER = 5

DATA_PATH = os.path.join(os.path.dirname(__file__), "../../CAERS_ASCII_2004_2017Q2.csv")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


# ---------------------------------------------------------------------------
# Data loading & preprocessing
# ---------------------------------------------------------------------------

def load_data(path: str) -> pd.DataFrame:
    """Load the CAERS CSV and drop rows without symptoms."""
    df = pd.read_csv(path, encoding="latin-1")
    df = df.dropna(subset=["SYM_One Row Coded Symptoms"])
    df = df.reset_index(drop=True)
    print(f"Loaded {len(df):,} reports with symptom data.")
    return df


def parse_symptoms(df: pd.DataFrame) -> pd.Series:
    """Split comma-separated symptom strings into lists of cleaned terms."""
    return df["SYM_One Row Coded Symptoms"].str.split(",").apply(
        lambda terms: [t.strip().upper() for t in terms if t.strip()]
    )


def build_symptom_matrix(
    symptom_lists: pd.Series, min_reports: int
) -> tuple[csr_matrix, np.ndarray]:
    """
    Build a binary report × symptom matrix, keeping only symptoms that
    appear in at least `min_reports` reports.

    Returns the sparse matrix and an array of kept symptom names.
    """
    from collections import Counter

    # Count symptom frequencies
    counts: Counter = Counter()
    for syms in symptom_lists:
        counts.update(set(syms))

    kept = sorted(s for s, c in counts.items() if c >= min_reports)
    symptom_to_idx = {s: i for i, s in enumerate(kept)}
    print(f"Kept {len(kept)} symptoms (appearing in >= {min_reports} reports).")

    rows, cols = [], []
    for row_idx, syms in enumerate(symptom_lists):
        for s in set(syms):
            if s in symptom_to_idx:
                rows.append(row_idx)
                cols.append(symptom_to_idx[s])

    mat = csr_matrix(
        (np.ones(len(rows), dtype=np.float32), (rows, cols)),
        shape=(len(symptom_lists), len(kept)),
    )
    return mat, np.array(kept)


# ---------------------------------------------------------------------------
# Dimensionality reduction & clustering
# ---------------------------------------------------------------------------

def run_umap(mat: csr_matrix, n_components: int, random_state: int) -> np.ndarray:
    """Reduce the symptom matrix with UMAP."""
    reducer = UMAP(
        n_components=n_components,
        metric="jaccard",
        random_state=random_state,
        n_neighbors=30,
        min_dist=0.0,
        verbose=False,
    )
    embedding = reducer.fit_transform(mat)
    print(f"UMAP embedding: {embedding.shape}")
    return embedding


def run_hdbscan(embedding: np.ndarray, min_cluster_size: int) -> np.ndarray:
    """Cluster the UMAP embedding with HDBSCAN."""
    clusterer = HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=10,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    labels = clusterer.fit_predict(embedding)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = (labels == -1).sum()
    print(f"HDBSCAN found {n_clusters} clusters; {n_noise:,} noise points "
          f"({n_noise / len(labels) * 100:.1f}%).")
    return labels


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------

def cluster_top_symptoms(
    mat: csr_matrix, symptom_names: np.ndarray, labels: np.ndarray, top_n: int = 10
) -> pd.DataFrame:
    """
    For each cluster, compute the most frequent symptoms and their lift
    (cluster frequency / overall frequency).
    """
    overall_freq = np.asarray(mat.mean(axis=0)).ravel()
    records = []

    for cid in sorted(set(labels)):
        if cid == -1:
            continue
        mask = labels == cid
        cluster_freq = np.asarray(mat[mask].mean(axis=0)).ravel()
        lift = np.where(overall_freq > 0, cluster_freq / overall_freq, 0.0)

        top_idx = np.argsort(-cluster_freq)[:top_n]
        top_syms = symptom_names[top_idx]
        top_freqs = cluster_freq[top_idx]
        top_lifts = lift[top_idx]

        records.append({
            "cluster": cid,
            "size": int(mask.sum()),
            "top_symptoms": ", ".join(top_syms),
            "top_symptom_freqs": ", ".join(f"{f:.2f}" for f in top_freqs),
            "top_symptom_lifts": ", ".join(f"{l:.2f}" for l in top_lifts),
        })

    return pd.DataFrame(records)


def cluster_industry_crosstab(
    df: pd.DataFrame, labels: np.ndarray, top_n: int = 5
) -> pd.DataFrame:
    """Show the top product industry names per cluster."""
    tmp = df.copy()
    tmp["cluster"] = labels
    tmp = tmp[tmp["cluster"] != -1]

    records = []
    for cid, grp in tmp.groupby("cluster"):
        top = grp["PRI_FDA Industry Name"].value_counts().head(top_n)
        records.append({
            "cluster": cid,
            "top_industries": ", ".join(
                f"{ind} ({cnt})" for ind, cnt in top.items()
            ),
        })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------

def plot_umap_clusters(
    embedding_2d: np.ndarray, labels: np.ndarray, output_path: str
) -> None:
    """Save a 2-D UMAP scatter plot colored by cluster label."""
    fig, ax = plt.subplots(figsize=(12, 9))

    noise_mask = labels == -1
    cluster_mask = ~noise_mask

    # Plot noise in light grey first
    ax.scatter(
        embedding_2d[noise_mask, 0],
        embedding_2d[noise_mask, 1],
        s=1, c="lightgrey", alpha=0.3, label="Noise",
    )

    # Plot clusters
    unique_labels = sorted(set(labels[cluster_mask]))
    palette = sns.color_palette("tab20", n_colors=max(len(unique_labels), 1))
    for i, cid in enumerate(unique_labels):
        mask = labels == cid
        ax.scatter(
            embedding_2d[mask, 0],
            embedding_2d[mask, 1],
            s=2, color=palette[i % len(palette)], alpha=0.5, label=f"Cluster {cid}",
        )

    ax.set_title("UMAP 2-D Projection of Adverse-Event Symptom Profiles")
    ax.set_xlabel("UMAP-1")
    ax.set_ylabel("UMAP-2")
    ax.legend(markerscale=5, fontsize=7, loc="best", ncol=2)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    print(f"Saved UMAP scatter plot to {output_path}")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main() -> None:
    np.random.seed(RANDOM_SEED)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Load & preprocess
    df = load_data(DATA_PATH)
    symptom_lists = parse_symptoms(df)
    mat, symptom_names = build_symptom_matrix(symptom_lists, MIN_SYMPTOM_REPORTS)

    # 2. UMAP – 5-D for clustering, 2-D for visualization
    print("\nRunning UMAP (5-D for clustering)...")
    embedding_5d = run_umap(mat, UMAP_N_COMPONENTS_CLUSTER, RANDOM_SEED)

    print("Running UMAP (2-D for visualization)...")
    embedding_2d = run_umap(mat, UMAP_N_COMPONENTS_VIZ, RANDOM_SEED)

    # 3. Cluster on the 5-D embedding
    print("\nRunning HDBSCAN...")
    labels = run_hdbscan(embedding_5d, MIN_CLUSTER_SIZE)

    # 4. Analysis
    print("\n" + "=" * 70)
    print("CLUSTER SUMMARIES")
    print("=" * 70)

    summary_df = cluster_top_symptoms(mat, symptom_names, labels)
    for _, row in summary_df.iterrows():
        print(f"\n--- Cluster {row['cluster']}  (n={row['size']:,}) ---")
        print(f"  Top symptoms : {row['top_symptoms']}")
        print(f"  Frequencies  : {row['top_symptom_freqs']}")
        print(f"  Lifts        : {row['top_symptom_lifts']}")

    industry_df = cluster_industry_crosstab(df, labels)
    print("\n" + "-" * 70)
    print("CLUSTER × INDUSTRY CROSS-REFERENCE")
    print("-" * 70)
    for _, row in industry_df.iterrows():
        print(f"  Cluster {row['cluster']}: {row['top_industries']}")

    # 5. Save outputs
    # Merge summaries
    out_df = summary_df.merge(industry_df, on="cluster", how="left")
    out_path_csv = os.path.join(OUTPUT_DIR, "cluster_assignments.csv")
    out_df.to_csv(out_path_csv, index=False)
    print(f"\nSaved cluster summary CSV to {out_path_csv}")

    out_path_png = os.path.join(OUTPUT_DIR, "umap_clusters.png")
    plot_umap_clusters(embedding_2d, labels, out_path_png)

    print("\nDone.")


if __name__ == "__main__":
    main()
