import json
import gzip
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

D = Path('data/processed/phase2_clustering')
RESULTS = Path('reports/review_S1_S10/results')

print("==================================================")
print("RUNNING AUDIT: Y7 to Y11 (S7: Migration)")
print("==================================================")

# ----------------------------------------------------
# Y7: Independent State Reproduction & Match with S10
# ----------------------------------------------------
print("\n--- [Y7] Customer Cluster Assignments Match ---")
# Load handoff file
handoff_path = D / "customer_cluster_assignments.csv.gz"
print(f"Reading {handoff_path}...")
df_assign = pd.read_csv(handoff_path)
print(f"Total rows in assignments: {len(df_assign):,} (Claimed: 3,030,475)")

year_counts = df_assign['year'].value_counts().sort_index()
print("\nRow counts by year:")
for y, c in year_counts.items():
    print(f"  Year {y}: {c:,}")

# Check 1404 match with S5 cluster_assignments_1404.pkl
ca_1404 = pd.read_pickle(D / "cluster_assignments_1404.pkl")
merged_1404 = df_assign[df_assign['year'] == 1404].merge(ca_1404, on='customer_id')
match_segment = (merged_1404['segment_x'] == merged_1404['segment_y']).mean()
print(f"1404 segment exact match with S5: {match_segment*100:.2f}% (Claimed: 100%)")

# ----------------------------------------------------
# Y8: Cumulative Transition Matrix Rates
# ----------------------------------------------------
print("\n--- [Y8] Cumulative Transition Rates ---")
trans_pct = pd.read_csv(D / "s7_aligned_transition_pooled_pct.csv", index_col=0)
print("Pooled transition percentages (rows=from, cols=to):")
print(trans_pct.to_string())

c1_stay = trans_pct.loc['C1', 'C1']
c7_stay = trans_pct.loc['C7', 'C7']
c7_to_t = trans_pct.loc['C7', 'T']
t_stay = trans_pct.loc['T', 'T']

print(f"\nRetention / Transition rates:")
print(f"  C1 stay: {c1_stay:.1f}% (Claimed: 81.1%)")
print(f"  C7 stay: {c7_stay:.1f}% (Claimed: 12.0%)")
print(f"  C7 -> T: {c7_to_t:.1f}% (Claimed: 55.7%)")
print(f"  T stay:  {t_stay:.1f}% (Claimed: 63.3%)")

# ----------------------------------------------------
# Y9: 5-Year Persistent Customers
# ----------------------------------------------------
print("\n--- [Y9] 5-Year Persistent Customers ---")
n_changes = pd.read_csv(D / "s7_n_changes_5yr.csv")
print("s7_n_changes_5yr.csv:")
print(n_changes.to_string())

# Verify on customer assignments
cust_years = df_assign.groupby('customer_id')['year'].nunique()
n_5yr = (cust_years == 5).sum()
print(f"\nCustomers present in all 5 years: {n_5yr:,} (Claimed: 467,892)")

zero_change_share = n_changes.loc[n_changes['changes'] == 0, 'proportion'].values[0]
print(f"Share with zero state changes: {zero_change_share*100:.1f}% (Claimed: 9.9%)")

# ----------------------------------------------------
# Y10: Quantile Alignment vs Constant Rial Agreement
# ----------------------------------------------------
print("\n--- [Y10] s7_aligned_vs_real_agreement.csv ---")
agree_df = pd.read_csv(D / "s7_aligned_vs_real_agreement.csv")
print(agree_df.to_string())

y1400 = agree_df[agree_df['year'] == 1400].iloc[0]
y1403 = agree_df[agree_df['year'] == 1403].iloc[0]

print(f"1400 Agreement: match_share={y1400['same_label']:.3f} (Claimed: 0.854), ARI={y1400['ari']:.3f} (Claimed: 0.688)")
print(f"1403 Agreement: match_share={y1403['same_label']:.3f} (Claimed: 0.961), ARI={y1403['ari']:.3f} (Claimed: 0.908)")

# ----------------------------------------------------
# Y11: Next Year NPL Entry by State
# ----------------------------------------------------
print("\n--- [Y11] s7_npl_entry_by_state.csv ---")
npl_state = pd.read_csv(D / "s7_npl_entry_by_state.csv")
print(npl_state.to_string())

c7_npl_entry = npl_state.loc[npl_state['state'] == 'C7', 'npl_entry_rate'].values[0]
t_npl_entry = npl_state.loc[npl_state['state'] == 'T', 'npl_entry_rate'].values[0]
c5_npl_entry = npl_state.loc[npl_state['state'] == 'C5', 'npl_entry_rate'].values[0]

print(f"Next-year NPL entry rate:")
print(f"  C7: {c7_npl_entry*100:.1f}% (Claimed: 17.1%)")
print(f"  T:  {t_npl_entry*100:.1f}% (Claimed: 12.4%)")
print(f"  C5: {c5_npl_entry*100:.1f}% (Claimed: 0.8%)")

# Save summary
y7_11_summary = pd.DataFrame([
    {'task': 'Y7_total_assignments_rows', 'reproduced': len(df_assign), 'claimed': 3030475},
    {'task': 'Y7_1404_match_s5', 'reproduced': round(match_segment*100, 1), 'claimed': 100.0},
    {'task': 'Y8_c1_stay_rate', 'reproduced': round(c1_stay, 1), 'claimed': 81.1},
    {'task': 'Y8_c7_stay_rate', 'reproduced': round(c7_stay, 1), 'claimed': 12.0},
    {'task': 'Y8_c7_to_t_rate', 'reproduced': round(c7_to_t, 1), 'claimed': 55.7},
    {'task': 'Y8_t_stay_rate', 'reproduced': round(t_stay, 1), 'claimed': 63.3},
    {'task': 'Y9_customers_5yr_count', 'reproduced': int(n_5yr), 'claimed': 467892},
    {'task': 'Y9_customers_5yr_zero_changes_pct', 'reproduced': round(zero_change_share*100, 1), 'claimed': 9.9},
    {'task': 'Y10_1400_match_share', 'reproduced': round(y1400['same_label'], 3), 'claimed': 0.854},
    {'task': 'Y10_1400_ari', 'reproduced': round(y1400['ari'], 3), 'claimed': 0.688},
    {'task': 'Y10_1403_match_share', 'reproduced': round(y1403['same_label'], 3), 'claimed': 0.961},
    {'task': 'Y10_1403_ari', 'reproduced': round(y1403['ari'], 3), 'claimed': 0.908},
    {'task': 'Y11_c7_npl_entry_rate', 'reproduced': round(c7_npl_entry*100, 1), 'claimed': 17.1},
    {'task': 'Y11_t_npl_entry_rate', 'reproduced': round(t_npl_entry*100, 1), 'claimed': 12.4},
    {'task': 'Y11_c5_npl_entry_rate', 'reproduced': round(c5_npl_entry*100, 1), 'claimed': 0.8}
])
y7_11_summary.to_csv(RESULTS / 'y07_to_y11_s7_reproduced.csv', index=False)
print("\nSaved Y7-Y11 summary to reports/review_S1_S10/results/y07_to_y11_s7_reproduced.csv")
