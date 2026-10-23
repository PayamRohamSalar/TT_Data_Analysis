import sys
sys.stdout.reconfigure(encoding='utf-8')
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.cluster import HDBSCAN

sys.path.insert(0, str(Path.cwd() / "src"))
from tt_bank.phase2_clustering.prep import Prep

t0 = time.time()
print("Reading data for SQ10 (HDBSCAN Audit)...")
F = pd.read_pickle("data/processed/phase2_clustering/features_customer_year.pkl")
M = F[F.category == "model"]
prep = Prep.from_json("data/processed/phase2_clustering/prep_spec.json")
A = M[M.y == 1404].reset_index(drop=True)
XA = prep.transform(A)

print(f"Loaded XA: {XA.shape}")

# 1. PCA variance explained
pca_full = PCA(n_components=14, random_state=0).fit(XA)
cum_var = np.cumsum(pca_full.explained_variance_ratio_)
print("\nPCA Cumulative Explained Variance:")
for i, cv in enumerate(cum_var, 1):
    print(f"Component {i}: {pca_full.explained_variance_ratio_[i-1]*100:.2f}% (Cumulative: {cv*100:.2f}%)")

var_6 = cum_var[5] * 100
var_8 = cum_var[7] * 100
print(f"\nExplained variance with 6 components: {var_6:.2f}%")
print(f"Explained variance with 8 components: {var_8:.2f}%")

# 2. HDBSCAN experiments on 40,000 subsample
rng = np.random.default_rng(42)
sub_idx = rng.choice(len(XA), 40000, replace=False)

# Transform with PCA 8
pca8 = PCA(n_components=8, random_state=0).fit(XA)
Z8 = pca8.transform(XA[sub_idx])

# Also transform with PCA 6 for comparison
pca6 = PCA(n_components=6, random_state=0).fit(XA)
Z6 = pca6.transform(XA[sub_idx])

experiments = [
    # Baseline setup with 6 components
    {"pca_n": 6, "Z": Z6, "mcs": 400, "ms": 50, "desc": "Orig config (6 comp, mcs=1%, ms=50)"},
    {"pca_n": 6, "Z": Z6, "mcs": 200, "ms": 15, "desc": "6 comp, smaller mcs & ms"},
    # 8 components setups
    {"pca_n": 8, "Z": Z8, "mcs": 400, "ms": 50, "desc": "8 comp, mcs=1%, ms=50"},
    {"pca_n": 8, "Z": Z8, "mcs": 200, "ms": 15, "desc": "8 comp, mcs=0.5%, ms=15"},
    {"pca_n": 8, "Z": Z8, "mcs": 100, "ms": 5, "desc": "8 comp, mcs=0.25%, ms=5"},
    {"pca_n": 8, "Z": Z8, "mcs": 50, "ms": 5, "desc": "8 comp, fine-grained (mcs=50, ms=5)"}
]

res_hdb = []
for exp in experiments:
    t_start = time.time()
    h = HDBSCAN(min_cluster_size=exp["mcs"], min_samples=exp["ms"], n_jobs=-1).fit(exp["Z"])
    labels = h.labels_
    noise_share = (labels == -1).mean() * 100
    clusters = labels[labels >= 0]
    n_cl = len(np.unique(clusters)) if len(clusters) > 0 else 0
    if n_cl > 0:
        sizes = pd.Series(clusters).value_counts().sort_values(ascending=False)
        top1_share = (sizes.iloc[0] / len(labels)) * 100
        min_cluster_share = (sizes.iloc[-1] / len(labels)) * 100
        size_str = ", ".join([f"C{i}:{cnt} ({cnt/len(labels)*100:.1f}%)" for i, cnt in sizes.head(5).items()])
    else:
        top1_share = 0
        min_cluster_share = 0
        size_str = "None"
    
    elapsed = time.time() - t_start
    print(f"\n--- {exp['desc']} ---")
    print(f"PCA components: {exp['pca_n']}, mcs: {exp['mcs']}, ms: {exp['ms']}")
    print(f"Clusters: {n_cl}, Noise: {noise_share:.2f}%, Top-1 cluster share: {top1_share:.2f}%")
    print(f"Cluster sizes: {size_str}")
    print(f"Time: {elapsed:.1f}s")
    
    res_hdb.append({
        "description": exp["desc"],
        "pca_components": exp["pca_n"],
        "min_cluster_size": exp["mcs"],
        "min_samples": exp["ms"],
        "n_clusters": n_cl,
        "noise_share_pct": noise_share,
        "top1_cluster_share_pct": top1_share,
        "min_cluster_share_pct": min_cluster_share,
        "runtime_s": elapsed
    })

df_hdb = pd.DataFrame(res_hdb)
df_hdb.to_csv("reports/review_S1_S4/results/sq10_hdbscan_audit.csv", index=False)
print("\nSaved SQ10 results to sq10_hdbscan_audit.csv")
