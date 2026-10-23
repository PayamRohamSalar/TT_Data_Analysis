import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import adjusted_rand_score
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

t0 = time.time()
D = Path('data/processed/phase2_clustering')
SEED = 20261022

print("Loading data for W10, W11, W12...")
F = pd.read_pickle(D / "features_customer_year.pkl")
pan = pd.read_pickle(D / "panel_customer_year.pkl")[["customer_id", "y", "bal_max"]]
F = F.merge(pan, on=["customer_id", "y"], how="left")
F["token_borrower"] = (F.category == "model") & F.has_primary_loan & ((F.turn_months < 3) | (F.bal_max < 5e6))
M = F[(F.category == "model") & ~F.token_borrower]
A = M[M.y == 1404].reset_index(drop=True)

# Load cluster assignments for 1404
ca = pd.read_pickle(D / "cluster_assignments_1404.pkl")
# Filter to main population (cluster in 1..8)
ca_main = ca[ca['customer_id'].isin(A['customer_id'])].sort_values('customer_id')
A_sorted = A.sort_values('customer_id').reset_index(drop=True)
ca_main = ca_main.reset_index(drop=True)

assert (A_sorted['customer_id'] == ca_main['customer_id']).all()
lab = ca_main['cluster'].to_numpy() - 1 # 0 to 7

# ---------- W10: Surrogate Tree Fidelity at Depths 4, 6, 8, 10
print("\n--- Running W10: Surrogate Tree Fidelity ---")
Xr = pd.DataFrame({
    "bal_mean_mtoman": A_sorted.bal_mean_r / 1e7,
    "bal_end_mtoman": A_sorted.bal_end_r / 1e7,
    "flow_total_mtoman": (A_sorted.cr_sum_r + A_sorted.db_sum_r) / 1e7,
    "txn_count": A_sorted.crn_sum + A_sorted.dbn_sum,
    "turn_share": A_sorted.turn_share,
    "flow_ratio": A_sorted.flow_ratio,
    "bal_cv": A_sorted.bal_cv,
    "bal_trend": A_sorted.bal_trend,
    "drawdown": A_sorted.drawdown,
    "acc_mean": A_sorted.acc_mean,
    "tenure_years": A_sorted.tenure_months / 12,
    "has_loan": A_sorted.has_loan_dec,
    "loan_mtoman": A_sorted.loan_dec_r / 1e7,
    "loan_to_dep": A_sorted.loan_to_dep,
    "npl_share": A_sorted.npl_share,
    "n_loans": A_sorted.n_loan_dec,
    "guar_mtoman": A_sorted.guar_dec_r / 1e7
})

rs = np.random.default_rng(SEED)
idx = rs.permutation(len(Xr))
tr, te = idx[: int(0.6 * len(idx))], idx[int(0.6 * len(idx)):]

tree_results = []
claimed_fids = {4: 0.76, 6: 0.84, 8: 0.87, 10: 0.89}
for depth in [4, 6, 8, 10]:
    dt = DecisionTreeClassifier(max_depth=depth, random_state=SEED).fit(Xr.iloc[tr], lab[tr])
    fid = float((dt.predict(Xr.iloc[te]) == lab[te]).mean())
    tree_results.append({
        'depth': depth,
        'fidelity_reproduced': round(fid, 4),
        'fidelity_claimed': claimed_fids[depth],
        'diff': round(fid - claimed_fids[depth], 4)
    })
    print(f"Depth {depth}: Fidelity={fid:.4f} (Claimed: {claimed_fids[depth]})")

df_tree = pd.DataFrame(tree_results)
df_tree.to_csv('reports/review_S1_S5b/results/w10_surrogate_tree_fidelity.csv', index=False)

# ---------- W11: ARI with M1 and M2
print("\n--- Running W11: ARI with M1 and M2 ---")
rfm = pd.read_pickle(D / "rfm_scores.pkl")
R = A_sorted[["customer_id", "y"]].merge(rfm[["customer_id", "y", "R", "F", "M", "L", "M_q", "F_q"]], on=["customer_id", "y"], how="left")
Mq, Fq, L_ = R.M_q.to_numpy(), R.F_q.to_numpy(), R.L.to_numpy()

m1 = np.full(len(R), 6)
done = np.zeros(len(R), bool)
for i, c in enumerate([
    (Mq == 5) & (Fq >= 4),
    (Mq >= 4) & (Fq >= 3),
    (L_ > 0) & (Fq >= 3),
    (L_ > 0) & (Fq < 3),
    (Mq >= 3) & (Fq < 3),
    (Mq <= 2) & (Fq >= 3)
]):
    mm = c & ~done
    m1[mm] = i
    done |= mm

RFMA = np.column_stack([R.R, R.F, R.M, R.L, A_sorted.has_loan_dec]).astype("float32")
from sklearn.cluster import KMeans
km2 = KMeans(7, n_init=30, random_state=SEED).fit(RFMA)
l2 = km2.labels_

ari_m1 = adjusted_rand_score(lab, m1)
ari_m2 = adjusted_rand_score(lab, l2)
print(f"ARI main vs M1: {ari_m1:.4f} (Claimed: 0.22)")
print(f"ARI main vs M2 (k=7): {ari_m2:.4f} (Claimed: 0.32)")

df_ari = pd.DataFrame([
    {'comparison': 'main_vs_M1', 'ari_reproduced': round(ari_m1, 4), 'ari_claimed': 0.22},
    {'comparison': 'main_vs_M2_k7', 'ari_reproduced': round(ari_m2, 4), 'ari_claimed': 0.32}
])
df_ari.to_csv('reports/review_S1_S5b/results/w11_ari_m1_m2.csv', index=False)

# ---------- W12: Inspect prep_spec_v2.json for Data Leakage and Annualization
print("\n--- Running W12: Inspect prep_spec_v2.json ---")
with open(D / "prep_spec_v2.json", "r", encoding="utf-8") as f:
    prep_spec = json.load(f)

print("prep_spec_v2 top keys:", list(prep_spec.keys()))
fit_year = prep_spec.get('fit_year')
fit_n = prep_spec.get('fit_n')
annualize_flag = prep_spec.get('annualize')
features_list = list(prep_spec.get('features', {}).keys())

print(f"fit_year: {fit_year}")
print(f"fit_n: {fit_n} (Matches 1404 main population 534,617?)")
print(f"annualize flag: {annualize_flag}")
print(f"Number of features in prep_spec: {len(features_list)}")

# Check if any fit statistics reference other years
leakage_found = False
for fname, fmeta in prep_spec.get('features', {}).items():
    if 'fit_year' in fmeta and fmeta['fit_year'] != 1404:
        print(f"WARNING: Feature {fname} fitted on year {fmeta['fit_year']}")
        leakage_found = True

w12_info = {
    'fit_year': fit_year,
    'fit_n': fit_n,
    'annualize_flag': annualize_flag,
    'n_features': len(features_list),
    'leakage_found': leakage_found,
    'features': features_list
}
with open('reports/review_S1_S5b/results/w12_prep_spec_audit.json', 'w', encoding='utf-8') as f:
    json.dump(w12_info, f, indent=2)
print("W12 audit complete.")
