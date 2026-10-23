import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, davies_bouldin_score
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

t0 = time.time()
D = Path('data/processed/phase2_clustering')
print("Loading features_customer_year.pkl and panel...")
F = pd.read_pickle(D / "features_customer_year.pkl")
pan = pd.read_pickle(D / "panel_customer_year.pkl")[["customer_id", "y", "bal_max"]]
F = F.merge(pan, on=["customer_id", "y"], how="left")
F["token_borrower"] = (F.category == "model") & F.has_primary_loan & ((F.turn_months < 3) | (F.bal_max < 5e6))
M = F[(F.category == "model") & ~F.token_borrower]
A = M[M.y == 1404].reset_index(drop=True)

from tt_bank.phase2_clustering.prep import Prep
print("Fitting Prep(annualize=True)...")
prep = Prep(annualize=True).fit(A, panel=M)
XA = prep.transform(A)
print(f"Prepared XA shape: {XA.shape} ({time.time()-t0:.1f}s)")

# Let's test subsample of 50,000 for fast verification
rng = np.random.default_rng(20261022)
N = len(XA)
sub_idx = rng.choice(N, size=50000, replace=False)
X_sub = XA[sub_idx]

results = []
for k in [6, 7, 8, 9, 10]:
    t_start = time.time()
    half1_idx = rng.choice(len(X_sub), size=len(X_sub)//2, replace=False)
    mask_h1 = np.zeros(len(X_sub), dtype=bool)
    mask_h1[half1_idx] = True
    mask_h2 = ~mask_h1
    
    km1 = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X_sub[mask_h1])
    km2 = KMeans(n_clusters=k, n_init=10, random_state=43).fit(X_sub[mask_h2])
    
    pred1 = km1.predict(X_sub)
    pred2 = km2.predict(X_sub)
    ari = adjusted_rand_score(pred1, pred2)
    
    km_full = KMeans(n_clusters=k, n_init=10, random_state=20261022).fit(X_sub)
    labels = km_full.labels_
    db = davies_bouldin_score(X_sub, labels)
    counts = np.bincount(labels)
    min_share = counts.min() / len(labels)
    
    elapsed = time.time() - t_start
    results.append({
        'k': k,
        'half_ari_reproduced_sub': round(ari, 4),
        'db_reproduced_sub': round(db, 3),
        'min_share_reproduced_sub': round(min_share, 4),
        'elapsed_sec': round(elapsed, 1)
    })
    print(f"k={k}: ARI={ari:.4f}, DB={db:.3f}, min_share={min_share*100:.2f}% ({elapsed:.1f}s)")

df_rep = pd.DataFrame(results)
df_rep.to_csv('reports/review_S1_S5b/results/w09_kselect_reproduced.csv', index=False)
print("Saved to reports/review_S1_S5b/results/w09_kselect_reproduced.csv")
