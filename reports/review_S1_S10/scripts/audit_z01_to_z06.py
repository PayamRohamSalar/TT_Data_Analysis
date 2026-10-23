import os
import glob
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, roc_auc_score
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

D = Path('data/processed/phase2_clustering')
RESULTS = Path('reports/review_S1_S10/results')
RESULTS.mkdir(parents=True, exist_ok=True)
SEED = 20261025

print("==================================================")
print("RUNNING AUDIT: Z1 to Z6 (Round 2 Remediation Checks)")
print("==================================================")

# ----------------------------------------------------
# Z1: Credit Lens v2 Verification & Circularity Test
# ----------------------------------------------------
print("\n--- [Z1] Credit Lens v2 & Circularity ---")
# 1. Inspect kselect v2
kselect_v2 = pd.read_csv(D / "s5b_credit_lens_v2_kselect.csv")
print("Credit Lens v2 kselect:")
print(kselect_v2.to_string())

# Check metrics for k=4
k4_row = kselect_v2[kselect_v2['k'] == 4].iloc[0]
print(f"k=4 claimed vs reproduced in CSV:")
print(f"  half_ari: {k4_row['half_ari']:.4f} (Claimed: ~0.72)")
print(f"  temporal_ari: {k4_row['temporal_ari']:.4f} (Claimed: 0.915)")
print(f"  auc_npl_entry: {k4_row['auc_npl_entry']:.4f} (Claimed: 0.60)")
print(f"  min_share: {k4_row['min_share']*100:.2f}% (Claimed: 3.8%)")

# Check ARI with main clusters
ca = pd.read_pickle(D / "cluster_assignments_1404.pkl")
ca_main = ca[ca['cluster'].isin(range(1, 9))]
c_v2_labels = pd.read_pickle(D / "credit_lens_v2_labels_1404.pkl")
merged_v2 = ca_main.merge(c_v2_labels, on='customer_id')
ari_main_v2 = adjusted_rand_score(merged_v2['cluster'], merged_v2['credit_lens'])
print(f"  ARI with main clusters: {ari_main_v2:.4f} (Claimed: 0.05)")

# 2. Check circularity of remaining performance features (late30, late90, mean_dpd, penalty)
print("\nTesting removal of performance features (late30, late90, mean_dpd, penalty)...")
# Let's inspect features used in 32_s5b_credit_lens_v2.py
F = pd.read_pickle(D / "features_customer_year.pkl")
pan = pd.read_pickle(D / "panel_customer_year.pkl")[["customer_id", "y", "bal_max"]]
F = F.merge(pan, on=["customer_id", "y"], how="left")
F["token_borrower"] = (F.category == "model") & F.has_primary_loan & ((F.turn_months < 3) | (F.bal_max < 5e6))

# Load ledger exact
lg = pd.read_pickle(D / "customer_month_ledger_exact.pkl")
lg["cid"] = lg.cid.astype("float64").astype("int64")
lg["y"] = (lg.due_ym // 100).astype(np.int16)
lg = lg[(lg.due_ym >= 140001) & (lg.due_ym <= 140412)]
la = lg.groupby(["cid", "y"]).agg(
    n_inst=("n_inst", "sum"), n_late=("n_late", "sum"), n_late30=("n_late30", "sum"),
    n_late90=("n_late90", "sum"), sum_dpd=("sum_dpd", "sum"), s_main=("s_main", "sum"),
    s_pen=("s_pen", "sum"), n_bad=("n_moaavagh", "sum"), n_mash=("n_mashkoo", "sum")
).reset_index().rename(columns={"cid": "customer_id"})

la["late30_x"] = la.n_late30 / la.n_inst
la["late90_x"] = la.n_late90 / la.n_inst
la["mean_dpd_x"] = (la.sum_dpd / la.n_inst).clip(-30, 365)
la["penalty_x"] = (la.s_pen / np.maximum(la.s_main, 1)).clip(0, 1)
F = F.merge(la[["customer_id", "y", "late30_x", "late90_x", "mean_dpd_x", "penalty_x"]], on=["customer_id", "y"], how="left")

POP = lambda y: F[(F.y == y) & (F.has_loan_dec == 1) & F.category.isin(["model", "newcomer"])].reset_index(drop=True)
A, B = POP(1404), POP(1403)

FEATS_ALL = [
    ("loan_log", lambda d: np.log1p(d.loan_dec_r.clip(lower=0)), "exposure"),
    ("loan_to_dep_log", lambda d: np.log1p(d.loan_to_dep.clip(lower=0)), "exposure"),
    ("n_loan_log", lambda d: np.log1p(d.n_loan_dec), "exposure"),
    ("loan_months", lambda d: d.loan_months / 12, "exposure"),
    ("guar_log", lambda d: np.log1p(d.guar_dec_r.clip(lower=0)), "exposure"),
    ("late30", lambda d: d.late30_x, "performance"),
    ("late90", lambda d: d.late90_x, "performance"),
    ("mean_dpd", lambda d: d.mean_dpd_x, "performance"),
    ("penalty", lambda d: d.penalty_x, "performance"),
    ("rate", lambda d: d.rate_w, "terms"),
    ("loan_age", lambda d: d.age_w / 12, "terms"),
    ("collateral", lambda d: d.coll_w, "terms"),
    ("duration", lambda d: d.duration_w / 365, "terms"),
    ("t_qard", lambda d: d.ltype_qard, "terms"),
    ("t_murabaha", lambda d: d.ltype_murabaha, "terms"),
    ("t_installment", lambda d: d.ltype_installment, "terms"),
    ("s_services", lambda d: d.sector_services, "sector"),
    ("s_industry", lambda d: d.sector_industry, "sector"),
    ("s_housing", lambda d: d.sector_housing, "sector"),
    ("s_agri", lambda d: d.sector_agri, "sector"),
    ("s_trade", lambda d: d.sector_trade, "sector"),
    ("dep_end_log", lambda d: np.log1p(d.bal_end_r.clip(lower=0)), "deposit"),
    ("dep_trend", lambda d: d.bal_trend, "deposit"),
    ("dep_turn", lambda d: d.turn_share, "deposit"),
    ("dep_drawdown", lambda d: d.drawdown, "deposit")
]

FEATS_NO_PERF = [f for f in FEATS_ALL if f[2] != 'performance']

def get_prepared_matrix(d, feat_list):
    X = pd.DataFrame({n: fn(d).astype(float).to_numpy() for n, fn, _ in feat_list})
    med = X.median()
    lo, hi = X.quantile(.005), X.quantile(.995)
    X = X.fillna(med).clip(lo, hi, axis=1)
    mu, sd = X.mean(), X.std().replace(0, 1)
    blocks = [b for _, _, b in feat_list]
    cnt = pd.Series(blocks).value_counts()
    w = np.array([1 / np.sqrt(cnt[b]) for b in blocks])
    return ((X - mu) / sd).to_numpy().astype("float32") * w

XA_all = get_prepared_matrix(A, FEATS_ALL)
XA_noperf = get_prepared_matrix(A, FEATS_NO_PERF)

# Quick clustering comparison on 50,000 sample
rng = np.random.default_rng(SEED)
sub_idx = rng.choice(len(A), size=50000, replace=False)
km_all = KMeans(4, n_init=15, random_state=SEED).fit(XA_all[sub_idx])
km_noperf = KMeans(4, n_init=15, random_state=SEED).fit(XA_noperf[sub_idx])

ari_perf_removal = adjusted_rand_score(km_all.labels_, km_noperf.labels_)
print(f"ARI between Credit Lens v2 and No-Performance Model (on 50k subsample): {ari_perf_removal:.4f}")

# Cross-prediction of NPL entry for both
N_next = F[F.y == 1404].set_index("customer_id")
nxt_B = N_next.reindex(B.customer_id.to_numpy())
present_B = B.customer_id.isin(N_next.index).to_numpy()
m_npl = (B.npl_share.to_numpy() == 0)
y_npl = present_B & (nxt_B.npl_share.fillna(0).to_numpy() > 0)

# Evaluate AUC on B for all vs noperf
XB_all = get_prepared_matrix(B, FEATS_ALL)
XB_noperf = get_prepared_matrix(B, FEATS_NO_PERF)

pred_B_all = km_all.predict(XB_all)
pred_B_noperf = km_noperf.predict(XB_noperf)

def calc_auc(pred_labels, y_true, mask):
    # Cluster average NPL rate as score
    rates = np.array([y_true[mask & (pred_labels == k)].mean() for k in range(4)])
    score = rates[pred_labels]
    return float(roc_auc_score(y_true[mask], score[mask]))

auc_all_rep = calc_auc(pred_B_all, y_npl, m_npl)
auc_noperf_rep = calc_auc(pred_B_noperf, y_npl, m_npl)
print(f"AUC for NPL entry with performance features: {auc_all_rep:.4f}")
print(f"AUC for NPL entry WITHOUT performance features: {auc_noperf_rep:.4f}")

# ----------------------------------------------------
# Z2: Check removal of 92.6% claim and search for old text
# ----------------------------------------------------
print("\n--- [Z2] Search for leftover '92.6' and 'بدون دفتر اقساط' ---")
md_files = glob.glob('reports/*.md') + glob.glob('docs/*.md')
z2_occurrences = []
for p in md_files:
    if 'review_S1_S5b' in p or 'review_S1_S10' in p:
        continue
    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
        for idx, line in enumerate(f, 1):
            if '92.6' in line or 'بدون دفتر اقساط' in line:
                z2_occurrences.append((p, idx, line.strip()))

print(f"Found {len(z2_occurrences)} occurrences in reports and docs:")
for r in z2_occurrences:
    print(f"  {r[0]}:{r[1]} -> {r[2][:100]}")

# Check s5b profile v2 for clusters 2 & 3 NPL share
c_prof_v2 = pd.read_csv(D / "s5b_credit_lens_v2_profile.csv")
print("\nCredit Lens v2 Profile:")
cols_to_show = [c for c in ['lens', 'borrowers', 'share_borrowers', 'loan_hemat', 'loan_share', 'npl_ratio', 'npl_share_of_total', 'share_token'] if c in c_prof_v2.columns]
print(c_prof_v2[cols_to_show].to_string())

c23_npl_share = c_prof_v2.loc[c_prof_v2['lens'].isin([2, 3]), 'npl_share_of_total'].sum()
print(f"\nSum of clusters 2 and 3 NPL share in v2: {c23_npl_share*100:.2f}% (Claimed: 85.9%)")

# ----------------------------------------------------
# Z3: Non-ledger borrowers in 1404 and NPL concentration
# ----------------------------------------------------
print("\n--- [Z3] 8.3% non-ledger borrowers and NPL analysis ---")
# In 1404, among primary borrowers (A):
# Has ledger row vs has no ledger row:
has_ledger = A['late30_x'].notna()
n_tot_borr = len(A)
n_no_ledger = (~has_ledger).sum()
pct_no_ledger = n_no_ledger / n_tot_borr * 100

total_npl_borr = A['npl_dec_r'].sum()
npl_no_ledger = A.loc[~has_ledger, 'npl_dec_r'].sum()
pct_npl_no_ledger = npl_no_ledger / total_npl_borr * 100

npl_rate_no_ledger = npl_no_ledger / A.loc[~has_ledger, 'loan_dec_r'].sum() * 100
npl_rate_has_ledger = A.loc[has_ledger, 'npl_dec_r'].sum() / A.loc[has_ledger, 'loan_dec_r'].sum() * 100

print(f"Primary borrowers in 1404: {n_tot_borr:,}")
print(f"No ledger rows in 1404: {n_no_ledger:,} ({pct_no_ledger:.2f}%, Claimed: 8.3%)")
print(f"Total NPL: {total_npl_borr/1e13:.2f} hemat; No ledger NPL: {npl_no_ledger/1e13:.2f} hemat ({pct_npl_no_ledger:.2f}%, Claimed: 67.5%)")
print(f"NPL ratio for NO-ledger: {npl_rate_no_ledger:.2f}% (Claimed: 27.2%)")
print(f"NPL ratio for HAS-ledger: {npl_rate_has_ledger:.2f}% (Claimed: 3.6%)")

# Test hypothesis: Do non-performing loans lack recent ledger rows?
# Let's inspect when their last installment was or if their loan is defaulted
print("\nTesting hypothesis 'وام‌های غیرجاری ردیف قسط تازه ندارند'...")
# Check distribution of npl_share among no_ledger vs has_ledger
print("Share with npl_share > 0 among no_ledger:", (A.loc[~has_ledger, 'npl_share'] > 0).mean() * 100)
print("Share with npl_share > 0 among has_ledger:", (A.loc[has_ledger, 'npl_share'] > 0).mean() * 100)

# ----------------------------------------------------
# Z4: Naming of C4, Removal of "خروج", Tree note
# ----------------------------------------------------
print("\n--- [Z4] Naming C4, Terminology, Tree Note ---")
cdef = pd.read_csv(D / "cluster_definitions.csv")
c4_name = cdef[cdef['segment'] == 'C4']['name_fa'].values[0]
print(f"Approved name for C4 in cluster_definitions.csv: '{c4_name}'")

# Search for any documents where C4 has another name
c4_wrong_occurrences = []
for p in md_files:
    if 'review_S1_S5b' in p or 'review_S1_S10' in p:
        continue
    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
        for idx, line in enumerate(f, 1):
            if 'C4' in line and 'وام‌های معوق' in line:
                c4_wrong_occurrences.append((p, idx, line.strip()))
print(f"Occurrences of old C4 name ('وام‌های معوق'): {len(c4_wrong_occurrences)}")
for r in c4_wrong_occurrences[:5]:
    print(f"  {r[0]}:{r[1]} -> {r[2][:100]}")

# ----------------------------------------------------
# Z5: Consistency of key numbers across S5 to S10
# ----------------------------------------------------
print("\n--- [Z5] Consistency of Key Numbers ---")
# Total population 1404:
pan_1404 = pan[pan['y'] == 1404]
F_1404 = F[F['y'] == 1404]
print(f"Total panel customers in 1404: {len(F_1404):,}")
total_deposit_1404 = F_1404['bal_end_r'].sum() / 1e13
total_loan_1404 = F_1404['loan_dec_r'].sum() / 1e13
total_npl_1404 = F_1404['npl_dec_r'].sum() / 1e13

print(f"Total Deposit in 1404: {total_deposit_1404:.2f} hemat (Expected: 84.77)")
print(f"Total Attributed Loans in 1404: {total_loan_1404:.2f} hemat (Expected: 124.97)")
print(f"Total Attributed NPL in 1404: {total_npl_1404:.2f} hemat (Expected: 10.66)")

# ----------------------------------------------------
# Z6: Verify previous review scripts exist
# ----------------------------------------------------
print("\n--- [Z6] Previous Review Scripts Preservation ---")
scripts_prev = glob.glob('reports/review_S1_S5b/scripts/*.py')
print(f"Found {len(scripts_prev)} python scripts in reports/review_S1_S5b/scripts/")

# Save consolidated results for Z1-Z6
z_summary = pd.DataFrame([
    {'check': 'Z1_kselect_v2_k4_half_ari', 'reproduced': round(k4_row['half_ari'], 4), 'claimed': 0.72},
    {'check': 'Z1_kselect_v2_k4_temporal_ari', 'reproduced': round(k4_row['temporal_ari'], 4), 'claimed': 0.915},
    {'check': 'Z1_kselect_v2_k4_auc_npl', 'reproduced': round(k4_row['auc_npl_entry'], 4), 'claimed': 0.60},
    {'check': 'Z1_kselect_v2_k4_min_share', 'reproduced': round(k4_row['min_share']*100, 2), 'claimed': 3.8},
    {'check': 'Z1_kselect_v2_ari_with_main', 'reproduced': round(ari_main_v2, 4), 'claimed': 0.05},
    {'check': 'Z2_v2_c23_npl_share', 'reproduced': round(c23_npl_share*100, 2), 'claimed': 85.9},
    {'check': 'Z3_no_ledger_share_pct', 'reproduced': round(pct_no_ledger, 2), 'claimed': 8.3},
    {'check': 'Z3_no_ledger_npl_share_pct', 'reproduced': round(pct_npl_no_ledger, 2), 'claimed': 67.5},
    {'check': 'Z3_no_ledger_npl_ratio_pct', 'reproduced': round(npl_rate_no_ledger, 2), 'claimed': 27.2},
    {'check': 'Z3_has_ledger_npl_ratio_pct', 'reproduced': round(npl_rate_has_ledger, 2), 'claimed': 3.6},
    {'check': 'Z5_total_deposit_hemat', 'reproduced': round(total_deposit_1404, 2), 'claimed': 84.77},
    {'check': 'Z5_total_loan_hemat', 'reproduced': round(total_loan_1404, 2), 'claimed': 124.97},
    {'check': 'Z5_total_npl_hemat', 'reproduced': round(total_npl_1404, 2), 'claimed': 10.66}
])
z_summary.to_csv(RESULTS / 'z_checks_reproduced.csv', index=False)
print("\nSaved Z1-Z6 summary to reports/review_S1_S10/results/z_checks_reproduced.csv")
