"""Empirical tests supporting answers to Special Questions (Q1 to Q17).
1. Q1: Noise sensitivity test on K-Means clusters (adding 5% and 10% Gaussian noise).
2. Q10: Cluster profiles inspection against approved names (C7 trend, LDR, etc.).
3. Q13: Roadmap tables/figures verification against phase2_plan.md.
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / "data" / "processed" / "phase2_clustering"
RESULTS = ROOT / "reports" / "review_S1_S10" / "results"

print("=" * 50)
print("RUNNING EMPIRICAL TESTS FOR SPECIAL QUESTIONS")
print("=" * 50)

# --- Test for Q1: Continuum & Noise Sensitivity ---
print("\n--- [Q1] Noise Sensitivity on 1404 Cluster Boundaries ---")
# Load prep spec and centers
prep_spec = json.load(open(D / "prep_spec_v2.json"))
centers = np.array(json.load(open(D / "s5_final_centers.json"))["centers_std"], dtype="float32")

# We can test on a 50k subsample of 1404 model customers
assign_1404 = pd.read_pickle(D / "cluster_assignments_1404.pkl")
c_model = assign_1404[assign_1404.segment.str.startswith("C")].copy()
print(f"Total model customers in 1404: {len(c_model):,}")

# Load transformed features or recompute distance
# In prep, let's load features_customer_year
F = pd.read_pickle(D / "features_customer_year.pkl")
F1404 = F[(F.y == 1404) & (F.customer_id.isin(c_model.customer_id))].set_index("customer_id")

from tt_bank.phase2_clustering.prep import Prep
prep = Prep.from_json(D / "prep_spec_v2.json")
sample_ids = np.random.RandomState(42).choice(c_model.customer_id, size=min(30000, len(c_model)), replace=False)
sub_df = F1404.loc[sample_ids].reset_index()

X_std = prep.transform(sub_df, aligned=False).astype("float32")
# Baseline labels
base_labels = ((X_std ** 2).sum(1)[:, None] - 2 * X_std @ centers.T + (centers ** 2).sum(1)[None, :]).argmin(1) + 1

# Test noise = 0.05 * std and 0.10 * std
rng = np.random.RandomState(42)
for sigma in [0.02, 0.05, 0.10]:
    X_noisy = X_std + rng.normal(0, sigma, size=X_std.shape).astype("float32")
    noisy_labels = ((X_noisy ** 2).sum(1)[:, None] - 2 * X_noisy @ centers.T + (centers ** 2).sum(1)[None, :]).argmin(1) + 1
    match_rate = (base_labels == noisy_labels).mean() * 100
    ari = adjusted_rand_score(base_labels, noisy_labels)
    print(f"Noise sigma={sigma:.2f}: label stability={match_rate:.1f}%, ARI={ari:.3f}")

# --- Test for Q10: Profile consistency check ---
print("\n--- [Q10] Cluster Profiles Consistency Check ---")
prof = pd.read_csv(D / "cluster_profiles.csv")
cols_to_show = ['segment', 'name_fa', 'bal_mean_mtoman', 'bal_trend', 'loan_to_deposit', 'npl_ratio', 'share_deposit', 'share_loan', 'share_npl']
avail_cols = [c for c in cols_to_show if c in prof.columns]
print(prof[avail_cols].to_string())

# Check C7 specifically
c7_row = prof[prof.segment == 'C7'].iloc[0]
print("\nC7 Profile Key Attributes:")
for col in ['name_fa', 'mean_trend', 'bal_trend', 'median_loan_to_dep', 'loan_to_deposit', 'npl_ratio', 'median_bal_mean_mtoman', 'median_bal_end_mtoman']:
    if col in prof.columns:
        print(f"  {col}: {c7_row[col]}")

# --- Test for Q13: Roadmap checklist check ---
print("\n--- [Q13] Deliverable Files Check ---")
expected_files = [
    "s5_cluster_sizes.csv",
    "s6_table_6_1.csv",
    "s6_table_6_2.csv",
    "s6_concentration.csv",
    "s7_pooled_transition_counts.csv",
    "s7_n_changes_5yr.csv",
    "s7_aligned_vs_real_agreement.csv",
    "s7_npl_entry_by_state.csv",
    "s8_province_segment_pct.csv",
    "s8_correlation_with_phase1.csv",
    "s8_branch_concentration.csv",
    "s9_deposit_band_test.csv",
    "s9_loan_band_test.csv",
    "s9_cluster_shares_weighted.csv",
    "s9_share_ranges.csv",
    "customer_cluster_assignments.csv.gz",
    "customer_cluster_attributes_1404.csv.gz",
    "cluster_definitions.csv",
    "cluster_profiles.csv",
    "cluster_transition_matrices.csv"
]
missing = [f for f in expected_files if not (D / f).exists()]
print(f"Expected files checked: {len(expected_files)}, Missing: {len(missing)}")
if missing:
    print(f"Missing files: {missing}")
else:
    print("All core expected output files exist in data/processed/phase2_clustering/")

print("\nEmpirical tests completed.")
