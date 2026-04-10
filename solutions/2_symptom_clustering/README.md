# Symptom Clustering / Syndrome Identification

Discovers latent clusters of co-occurring adverse-event symptoms in the FDA CAERS dataset, potentially revealing unrecognized syndromes.

## Approach

1. **Preprocessing** — Parse comma-separated MedDRA symptom terms into a binary report × symptom matrix; filter to symptoms appearing in ≥ 50 reports.
2. **Dimensionality reduction** — UMAP with Jaccard distance (5-D for clustering, 2-D for visualization).
3. **Clustering** — HDBSCAN (`min_cluster_size=100`) on the 5-D embedding.
4. **Analysis** — Each cluster is characterized by its top symptoms (frequency + lift over baseline), cross-referenced with FDA industry codes, and visualized on a 2-D UMAP scatter plot.

## Usage

```bash
pip install pandas numpy scikit-learn umap-learn hdbscan matplotlib seaborn
python main.py
```

## Outputs (written to `output/`)

| File | Description |
|---|---|
| `umap_clusters.png` | 2-D UMAP scatter plot colored by cluster |
| `cluster_assignments.csv` | Cluster ID, size, top symptoms, frequencies, lifts, and top industries |
