import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

t0 = time.time()
D = Path('data/processed/phase2_clustering')
SEED = 20261024

print("Loading data for W16...")
F = pd.read_pickle(D / "features_customer_year.pkl")
pan = pd.read_pickle(D / "panel_customer_year.pkl")[["customer_id", "y", "bal_max"]]
F = F.merge(pan, on=["customer_id", "y"], how="left")
F["token_borrower"] = (F.category == "model") & F.has_primary_loan & ((F.turn_months < 3) | (F.bal_max < 5e6))

# Ledger exact
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
la["bad_x"] = (la.n_bad + la.n_mash) / la.n_inst

F = F.merge(la[["customer_id", "y", "late30_x", "late90_x", "mean_dpd_x", "penalty_x", "bad_x"]], on=["customer_id", "y"], how="left")

POP = lambda y: F[(F.y == y) & (F.has_loan_dec == 1) & F.category.isin(["model", "newcomer"])].reset_index(drop=True)
A = POP(1404)

FEATS = [
    ("loan_log", lambda d: np.log1p(d.loan_dec_r.clip(lower=0)), "exposure"),
    ("loan_to_dep_log", lambda d: np.log1p(d.loan_to_dep.clip(lower=0)), "exposure"),
    ("n_loan_log", lambda d: np.log1p(d.n_loan_dec), "exposure"),
    ("loan_months", lambda d: d.loan_months / 12, "exposure"),
    ("guar_log", lambda d: np.log1p(d.guar_dec_r.clip(lower=0)), "exposure"),
    ("npl_share", lambda d: d.npl_share, "performance"),
    ("late30", lambda d: d.late30_x, "performance"),
    ("late90", lambda d: d.late90_x, "performance"),
    ("mean_dpd", lambda d: d.mean_dpd_x, "performance"),
    ("bad_status", lambda d: d.bad_x, "performance"),
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

def raw(d):
    X = pd.DataFrame({n: fn(d).astype(float).to_numpy() for n, fn, _ in FEATS})
    X["no_contract_attr"] = d.rate_w.isna().astype(float).to_numpy()
    X["no_ledger"] = d.late30_x.isna().astype(float).to_numpy()
    return X

RA = raw(A)
med = RA.median()
lo, hi = RA.quantile(.005), RA.quantile(.995)
cols = list(RA.columns)
blocks = [b for _, _, b in FEATS] + ["flags", "flags"]
cnt = pd.Series(blocks).value_counts()
w = np.array([1 / np.sqrt(cnt[b]) for b in blocks])

def prep(d):
    X = raw(d).fillna(med)
    X = X.clip(lo, hi, axis=1)
    mu = RA.fillna(med).clip(lo, hi, axis=1).mean()
    sd = RA.fillna(med).clip(lo, hi, axis=1).std().replace(0, 1)
    return ((X - mu) / sd).to_numpy().astype("float32") * w

XA = prep(A)

# Load existing credit lens labels
cred_labels_df = pd.read_pickle(D / "credit_lens_labels_1404.pkl")
# Ensure alignment
cred_labels_df = cred_labels_df.set_index('customer_id').reindex(A['customer_id']).reset_index()
orig_labels = cred_labels_df['credit_lens'].to_numpy() - 1 # 0 to 4

# ---------- 1. Variance Decomposition (Between-cluster SS per feature)
print("\n--- Variance Decomposition across clusters ---")
grand_mean = XA.mean(axis=0)
k_counts = np.bincount(orig_labels)
centers = np.array([XA[orig_labels == k].mean(axis=0) for k in range(5)])

ssb_per_feat = np.zeros(XA.shape[1])
sst_per_feat = ((XA - grand_mean)**2).sum(axis=0)

for k in range(5):
    ssb_per_feat += k_counts[k] * ((centers[k] - grand_mean)**2)

eta2_per_feat = ssb_per_feat / sst_per_feat
total_ssb = ssb_per_feat.sum()
share_of_total_ssb = ssb_per_feat / total_ssb

var_df = pd.DataFrame({
    'feature': cols,
    'block': blocks,
    'weight': w,
    'SSB': ssb_per_feat,
    'SST': sst_per_feat,
    'eta_squared': eta2_per_feat,
    'share_of_separation_pct': share_of_total_ssb * 100
}).sort_values('share_of_separation_pct', ascending=False)

print(var_df.head(10).to_string(index=False))

flags_share = var_df[var_df['block'] == 'flags']['share_of_separation_pct'].sum()
print(f"\nTotal share of separation variance from flags (no_contract_attr + no_ledger): {flags_share:.2f}%")

# ---------- 2. Fit K-Means WITHOUT the two flag columns
print("\n--- Fitting K-Means WITHOUT no_contract_attr and no_ledger ---")
blocks_noflag = [b for _, _, b in FEATS]
cnt_noflag = pd.Series(blocks_noflag).value_counts()
w_noflag = np.array([1 / np.sqrt(cnt_noflag[b]) for b in blocks_noflag])

def prep_noflag(d):
    X = pd.DataFrame({n: fn(d).astype(float).to_numpy() for n, fn, _ in FEATS})
    med_nf = X.median()
    lo_nf, hi_nf = X.quantile(.005), X.quantile(.995)
    X = X.fillna(med_nf).clip(lo_nf, hi_nf, axis=1)
    mu = X.mean()
    sd = X.std().replace(0, 1)
    return ((X - mu) / sd).to_numpy().astype("float32") * w_noflag

XA_noflag = prep_noflag(A)

km_noflag = KMeans(5, n_init=20, random_state=SEED).fit(XA_noflag)
labels_noflag = km_noflag.labels_

ari_noflag = adjusted_rand_score(orig_labels, labels_noflag)
print(f"\nARI between original credit lens and model WITHOUT flags: {ari_noflag:.4f}")

# Cross-tabulation between original clusters and no-flag clusters
ct = pd.crosstab(pd.Series(orig_labels + 1, name='orig_credit_lens'), pd.Series(labels_noflag + 1, name='noflag_cluster'))
print("\nCross-tabulation (Orig vs No-Flag):")
print(ct)

var_df.to_csv('reports/review_S1_S5b/results/w16_credit_lens_variance_decomposition.csv', index=False)
ct.to_csv('reports/review_S1_S5b/results/w16_crosstab_orig_vs_noflag.csv')
print("W16 results saved.")
