import sys
sys.stdout.reconfigure(encoding='utf-8')
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score

sys.path.insert(0, str(Path.cwd() / "src"))
from tt_bank.phase2_clustering.prep import Prep

t0 = time.time()
print("Reading data for SQ9 (K-Means Seed Sensitivity with n_init=30)...")
F = pd.read_pickle("data/processed/phase2_clustering/features_customer_year.pkl")
M = F[F.category == "model"]
prep = Prep.from_json("data/processed/phase2_clustering/prep_spec.json")

A = M[M.y == 1404].reset_index(drop=True)
B = M[M.y == 1403].reset_index(drop=True)

XA = prep.transform(A)
XB = prep.transform(B)
print(f"Data ready: XA={XA.shape}, XB={XB.shape} in {time.time()-t0:.1f}s")

rng = np.random.default_rng(42)

# Load existing scorecard values for M3
sc = pd.read_csv("data/processed/phase2_clustering/s4_scorecard_full.csv")
sc_m3 = sc[sc["method"] == "M3"].set_index("k")

results = []

for k in [7, 8, 9]:
    print(f"\n--- Testing M3 with k={k} (n_init=30) ---")
    t_start = time.time()
    
    # 1. Full dataset fits with n_init=30
    mA = KMeans(k, n_init=30, random_state=0).fit(XA)
    lA = mA.predict(XA)
    
    mB = KMeans(k, n_init=30, random_state=0).fit(XB)
    lBA = mB.predict(XA)
    
    temporal_ari_30 = float(adjusted_rand_score(lA, lBA))
    
    # 2. Half-sample stability with n_init=30 (average of 2 reps like 22_s4_run_basket.py)
    half_aris_30 = []
    for r in range(2):
        perm = rng.permutation(len(XA))
        h1, h2 = perm[: len(XA) // 2], perm[len(XA) // 2:]
        m1 = KMeans(k, n_init=30, random_state=r).fit(XA[h1])
        m2 = KMeans(k, n_init=30, random_state=r + 100).fit(XA[h2])
        half_aris_30.append(adjusted_rand_score(m1.predict(XA), m2.predict(XA)))
    
    half_ari_30 = float(np.mean(half_aris_30))
    
    # Compare with original (n_init=3 in half-sample, n_init=10 in temporal)
    orig_half = sc_m3.loc[k, "half_ari"] if k in sc_m3.index else np.nan
    orig_temp = sc_m3.loc[k, "temporal_ari"] if k in sc_m3.index else np.nan
    
    print(f"k={k}: Temporal ARI (orig n_init=10) = {orig_temp:.4f} -> (n_init=30) = {temporal_ari_30:.4f}")
    print(f"k={k}: Half-Sample ARI (orig n_init=3) = {orig_half:.4f} -> (n_init=30) = {half_ari_30:.4f}")
    print(f"Time for k={k}: {time.time()-t_start:.1f}s")
    
    results.append({
        "k": k,
        "orig_half_ari_ninit3": orig_half,
        "new_half_ari_ninit30": half_ari_30,
        "half_ari_diff": half_ari_30 - orig_half,
        "orig_temporal_ari_ninit10": orig_temp,
        "new_temporal_ari_ninit30": temporal_ari_30,
        "temporal_ari_diff": temporal_ari_30 - orig_temp
    })

df_res = pd.DataFrame(results)
print("\n--- Summary of K-Means Seed Sensitivity (SQ9) ---")
print(df_res.to_string(index=False))
df_res.to_csv("reports/review_S1_S4/results/sq09_kmeans_seed_sensitivity.csv", index=False)
print("Saved to sq09_kmeans_seed_sensitivity.csv")
