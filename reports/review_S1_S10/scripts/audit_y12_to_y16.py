"""Independent audit of S8: Geography (Tasks Y12 to Y16)
Audits coverage, Cramer's V, Phase 1 correlation, Headquarters & Independent branches, and Branch concentration.
Saves reproduced results to reports/review_S1_S10/results/y12_to_y16_s8_reproduced.csv.
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, chi2_contingency

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / "data" / "processed" / "phase2_clustering"
P1 = ROOT / "data" / "processed" / "phase1_market_overview"
RESULTS = ROOT / "reports" / "review_S1_S10" / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

print("=" * 50)
print("RUNNING AUDIT: Y12 to Y16 (S8: Geography)")
print("=" * 50)

norm = lambda s: s.replace("ي", "ی").replace("ك", "ک").replace("‌", " ").strip()
H = 1e13
SEG = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "T", "I", "N", "S"]

# Load features and segment assignments for 1404
print("Loading data/processed/phase2_clustering/features_customer_year.pkl and cluster_assignments_1404.pkl...")
F = pd.read_pickle(D / "features_customer_year.pkl")
F = F[F.y == 1404]
seg = pd.read_pickle(D / "cluster_assignments_1404.pkl")[["customer_id", "segment"]]

G = F.merge(seg, on="customer_id")
G["segment"] = G.segment.replace({"O": "I"})
G["province"] = G.province.map(lambda s: norm(s) if isinstance(s, str) else s)
G["dep"] = G.bal_dec.fillna(0)
G["loan"] = G.loan_dec_r.fillna(0)
G["npl"] = G.npl_dec_r.fillna(0)

N = len(G)
A = G[G.province.notna()].copy()

# ----------------------------------------------------
# Y12: Coverage of Province/Branch
# ----------------------------------------------------
print("\n--- [Y12] Coverage Analysis ---")
cust_cov = len(A) / N * 100
dep_cov = A.dep.sum() / G.dep.sum() * 100
loan_cov = A.loan.sum() / G.loan.sum() * 100
npl_cov = A.npl.sum() / G.npl.sum() * 100

print(f"Overall Coverage:")
print(f"  Customers: {cust_cov:.1f}% ({len(A):,} / {N:,}) (Claimed: 84.5%)")
print(f"  Deposit:   {dep_cov:.1f}% (Claimed: 91.0%)")
print(f"  Loans:     {loan_cov:.1f}% (Claimed: 98.7%)")
print(f"  NPL:       {npl_cov:.1f}%")

c6_g = G[G.segment == 'C6']
c6_cov = c6_g.province.notna().mean() * 100
print(f"C6 Customer Coverage: {c6_cov:.1f}% (Claimed: 47.4%)")

# Also check s8_coverage_by_segment.csv
cov_csv = pd.read_csv(D / "s8_coverage_by_segment.csv", index_col=0)
print("\ns8_coverage_by_segment.csv C6 row:")
print(cov_csv.loc['C6'].to_dict())

# ----------------------------------------------------
# Y13: Cramer's V Province x Cluster
# ----------------------------------------------------
print("\n--- [Y13] Cramer's V Province x Cluster ---")
ct = pd.crosstab(A.province, A.segment).reindex(columns=SEG).fillna(0).astype(int)
ct_core = ct.loc[~ct.index.isin(["ستاد", "شعب مستقل"])]
chi2, pval, dof, _ = chi2_contingency(ct_core.to_numpy())
min_dim = min(ct_core.shape) - 1
cramers_v = np.sqrt(chi2 / (ct_core.to_numpy().sum() * min_dim))
print(f"Chi2: {chi2:.2f}, p-val: {pval:.4e}, n: {ct_core.to_numpy().sum():,}")
print(f"Cramer's V: {cramers_v:.3f} (Claimed: 0.058)")

# ----------------------------------------------------
# Y14: Spearman Rank Correlation with Phase 1 (31 Provinces)
# ----------------------------------------------------
print("\n--- [Y14] Spearman Rank Correlation with Phase 1 ---")
p1_corr = pd.read_csv(D / "s8_correlation_with_phase1.csv", index_col=0)
print("s8_correlation_with_phase1.csv:")
print(p1_corr.to_string())

# Recompute directly
rows = []
for p, g in A.groupby("province"):
    rows.append(dict(
        province=p,
        deposit_hemat=g.dep.sum() / H,
        loan_hemat=g.loan.sum() / H,
        npl_ratio=g.npl.sum() / g.loan.sum() * 100 if g.loan.sum() > 0 else np.nan,
        ldr=g.loan.sum() / g.dep.sum() * 100 if g.dep.sum() > 0 else np.nan
    ))
PI = pd.DataFrame(rows).set_index("province")
P1d = pd.read_csv(P1 / "ch7_province_indicators.csv", encoding="utf-8-sig")
P1d["province"] = P1d.province.map(norm)
P1d = P1d.set_index("province")
J = PI.join(P1d[["res_share", "loan_share", "ldr", "npl_ratio"]].add_prefix("p1_"), how="left")
core = J[J.p1_res_share.notna()]
print(f"Core provinces matched with Phase 1: {len(core)} (Claimed: 31)")

r_npl, p_npl = spearmanr(core["npl_ratio"], core["p1_npl_ratio"])
r_ldr, p_ldr = spearmanr(core["ldr"], core["p1_ldr"])
r_dep, p_dep = spearmanr(core["deposit_hemat"], core["p1_res_share"])
r_loan, p_loan = spearmanr(core["loan_hemat"], core["p1_loan_share"])

print(f"Spearman correlations:")
print(f"  NPL Ratio:        r = {r_npl:.3f} (Claimed: 0.87)")
print(f"  Loan-to-Deposit:  r = {r_ldr:.3f} (Claimed: 0.90)")
print(f"  Resource Share:   r = {r_dep:.3f} (Claimed: 0.96)")
print(f"  Loan Share:       r = {r_loan:.3f} (Claimed: 0.98)")

# ----------------------------------------------------
# Y15: Headquarters (ستاد) & Independent Branches (شعب مستقل)
# ----------------------------------------------------
print("\n--- [Y15] Headquarters & Independent Branches ---")
setad = A[A.province == "ستاد"]
shob_mostaghel = A[A.province == "شعب مستقل"]

setad_cust = len(setad)
setad_dep = setad.dep.sum() / H
setad_loan = setad.loan.sum() / H
setad_npl = setad.npl.sum() / H
setad_c1s_pct = setad.segment.isin(["C1", "S"]).mean() * 100

shob_cust = len(shob_mostaghel)
shob_dep = shob_mostaghel.dep.sum() / H
shob_loan = shob_mostaghel.loan.sum() / H
shob_npl = shob_mostaghel.npl.sum() / H

print(f"Headquarters (ستاد):")
print(f"  Customers: {setad_cust:,} (Claimed: 2,427)")
print(f"  Loans:     {setad_loan:.2f} hemat (Claimed: 12.78)")
print(f"  Deposits:  {setad_dep:.2f} hemat (Claimed: 0.94)")
print(f"  NPL:       {setad_npl:.3f} hemat, NPL ratio: {setad.npl.sum()/setad.loan.sum()*100:.2f}%")
print(f"  C1+S Share: {setad_c1s_pct:.1f}% (Claimed: 98.3%)")

print(f"Independent Branches (شعب مستقل):")
print(f"  Customers: {shob_cust:,} (Claimed: 3,765)")
print(f"  Deposits:  {shob_dep:.2f} hemat (Claimed: 9.91)")
print(f"  Loans:     {shob_loan:.2f} hemat (Claimed: 11.01)")
print(f"  NPL:       {shob_npl:.2f} hemat")

# ----------------------------------------------------
# Y16: Branch Concentration
# ----------------------------------------------------
print("\n--- [Y16] Branch Concentration ---")
br = A.groupby("home_branch").agg(customers=("customer_id", "size"), dep=("dep", "sum"), loan=("loan", "sum"), npl=("npl", "sum"))
nb = len(br)
def topshare(v, f):
    v = np.sort(v.to_numpy())[::-1]
    return v[: max(1, int(round(nb * f)))].sum() / v.sum()

top10_npl = topshare(br['npl'], 0.10) * 100
top10_dep = topshare(br['dep'], 0.10) * 100
top10_cust = topshare(br['customers'], 0.10) * 100

print(f"Top 10% Branches Share:")
print(f"  NPL:       {top10_npl:.1f}% (Claimed: 77.2%)")
print(f"  Deposit:   {top10_dep:.1f}% (Claimed: 57.9%)")
print(f"  Customers: {top10_cust:.1f}% (Claimed: 22.6%)")

# Save summary
y12_16_summary = pd.DataFrame([
    {'task': 'Y12_customer_coverage_pct', 'reproduced': round(cust_cov, 1), 'claimed': 84.5},
    {'task': 'Y12_deposit_coverage_pct', 'reproduced': round(dep_cov, 1), 'claimed': 91.0},
    {'task': 'Y12_loan_coverage_pct', 'reproduced': round(loan_cov, 1), 'claimed': 98.7},
    {'task': 'Y12_c6_coverage_pct', 'reproduced': round(c6_cov, 1), 'claimed': 47.4},
    {'task': 'Y13_cramers_v', 'reproduced': round(cramers_v, 3), 'claimed': 0.058},
    {'task': 'Y14_spearman_npl', 'reproduced': round(r_npl, 2), 'claimed': 0.87},
    {'task': 'Y14_spearman_ldr', 'reproduced': round(r_ldr, 2), 'claimed': 0.90},
    {'task': 'Y14_spearman_dep_res', 'reproduced': round(r_dep, 2), 'claimed': 0.96},
    {'task': 'Y14_spearman_loan_share', 'reproduced': round(r_loan, 2), 'claimed': 0.98},
    {'task': 'Y15_setad_customers', 'reproduced': int(setad_cust), 'claimed': 2427},
    {'task': 'Y15_setad_loan_hemat', 'reproduced': round(setad_loan, 2), 'claimed': 12.78},
    {'task': 'Y15_shob_customers', 'reproduced': int(shob_cust), 'claimed': 3765},
    {'task': 'Y15_shob_dep_hemat', 'reproduced': round(shob_dep, 2), 'claimed': 9.91},
    {'task': 'Y16_top10_npl_share_pct', 'reproduced': round(top10_npl, 1), 'claimed': 77.2},
    {'task': 'Y16_top10_dep_share_pct', 'reproduced': round(top10_dep, 1), 'claimed': 57.9},
    {'task': 'Y16_top10_cust_share_pct', 'reproduced': round(top10_cust, 1), 'claimed': 22.6}
])
y12_16_summary.to_csv(RESULTS / 'y12_to_y16_s8_reproduced.csv', index=False)
print("\nSaved Y12-Y16 summary to reports/review_S1_S10/results/y12_to_y16_s8_reproduced.csv")
