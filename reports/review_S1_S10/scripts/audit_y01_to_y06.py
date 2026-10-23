import pandas as pd
import numpy as np
from pathlib import Path
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

D = Path('data/processed/phase2_clustering')
RESULTS = Path('reports/review_S1_S10/results')

print("==================================================")
print("RUNNING AUDIT: Y1 to Y6 (S6: Value and Risk)")
print("==================================================")

# Load S6 generated tables
t61 = pd.read_csv(D / "s6_table_6_1.csv")
t62 = pd.read_csv(D / "s6_table_6_2.csv")
s6_conc = pd.read_csv(D / "s6_concentration.csv")

print("\n--- [Y1 & Y2] s6_table_6_1.csv ---")
print(t61.to_string())

# Verify Y1 totals
tot_dep = t61['deposit_hemat'].sum()
tot_loan = t61['loan_hemat'].sum()
tot_npl = t61['npl_hemat'].sum()

print(f"\nTotals from Table 6-1:")
print(f"  Deposit: {tot_dep:.2f} hemat (Claimed: 84.77)")
print(f"  Attributed Loans: {tot_loan:.2f} hemat (Claimed: 124.97)")
print(f"  Attributed NPL: {tot_npl:.2f} hemat (Claimed: 10.66)")

# Check sum of share columns
print(f"  Sum share_customers: {t61['share_customers'].sum():.4f}")
print(f"  Sum share_deposit: {t61['share_deposit'].sum():.4f}")
print(f"  Sum share_loan: {t61['share_loan'].sum():.4f}")
print(f"  Sum share_npl: {t61['share_npl'].sum():.4f}")

# Verify Y2 cluster shares
c1_row = t61[t61['segment'] == 'C1'].iloc[0]
t_row = t61[t61['segment'] == 'T'].iloc[0]
c4_row = t61[t61['segment'] == 'C4'].iloc[0]

print(f"\nC1 Shares:")
print(f"  Deposit: {c1_row['share_deposit']*100:.2f}% (Claimed: 60.8%)")
print(f"  Loan: {c1_row['share_loan']*100:.2f}% (Claimed: 51.4%)")
print(f"  NPL: {c1_row['share_npl']*100:.2f}% (Claimed: 37.5%)")

print(f"\nT Shares:")
print(f"  Loan: {t_row['share_loan']*100:.2f}% (Claimed: 8.7%)")
print(f"  NPL: {t_row['share_npl']*100:.2f}% (Claimed: 30.1%)")
print(f"  NPL Ratio: {t_row['npl_ratio']*100:.2f}% (Claimed: 29.7%)")

print(f"\nC4 Shares:")
print(f"  NPL Share: {c4_row['share_npl']*100:.2f}% (Claimed: 10.1%)")
# Number of borrowers in C4:
n_borr_c4 = int(round(c4_row['customers'] * c4_row['share_borrowers'])) if 'share_borrowers' in c4_row else int(round(c4_row['customers'] * c4_row['share_with_loan']))
print(f"  Borrowers in C4: {n_borr_c4:,} (Claimed: 1,223)")

# Verify Y3 Concentration & Gini
print("\n--- [Y3] s6_concentration.csv ---")
print(s6_conc.to_string())

# Verify Y4 Cross-sell Capacity (Table 6-2)
print("\n--- [Y4] s6_table_6_2.csv ---")
print(t62.to_string())

c1_x_row = t62[t62['segment'] == 'C1'].iloc[0]
c3_x_row = t62[t62['segment'] == 'C3'].iloc[0]
print(f"C1 Cross-sell candidates (bal >= 100M Toman): {int(c1_x_row['eligible_100mt']):,} (Claimed: 10,135); Deposit: {c1_x_row['eligible_100mt_deposit_hemat']:.2f} hemat (Claimed: 28.13)")
print(f"C3 Cross-sell candidates (bal >= 100M Toman): {int(c3_x_row['eligible_100mt']):,} (Claimed: 7,166); Deposit: {c3_x_row['eligible_100mt_deposit_hemat']:.2f} hemat (Claimed: 6.0)")

# Verify Y5 Installment Delay > 30 days
print("\n--- [Y5] Installment Delay > 30 days ---")
print(f"C1 late30: {c1_row['late30']*100:.2f}% (Claimed: 15.2%)")
print(f"C4 late30: {c4_row['late30']*100:.2f}% (Claimed: 47.3%)")
c7_row = t61[t61['segment'] == 'C7'].iloc[0]
print(f"C7 late30: {c7_row['late30']*100:.2f}% (Claimed: 52.3%)")
print(f"T late30: {t_row['late30']*100:.2f}% (Claimed: 59.8%)")

# Verify Y6 Interest Paid Index
print("\n--- [Y6] Interest Paid to Deposit Index ---")
s_row = t61[t61['segment'] == 'S'].iloc[0]
c8_row = t61[t61['segment'] == 'C8'].iloc[0]
print(f"C1 interest index: {c1_row['interest_per_deposit']*100:.2f}% (Claimed: 7.7%)")
print(f"S interest index: {s_row['interest_per_deposit']*100:.2f}% (Claimed: 9.8%)")
print(f"C8 interest index: {c8_row['interest_per_deposit']*100:.2f}% (Claimed: 1.5%)")

# Calculate Gini independently on features
def gini(array):
    array = np.sort(np.asarray(array, dtype=float))
    index = np.arange(1, array.shape[0] + 1)
    n = array.shape[0]
    return float((np.sum((2 * index - n  - 1) * array)) / (n * np.sum(array)))

F = pd.read_pickle(D / "features_customer_year.pkl")
F_1404 = F[F['y'] == 1404]
gini_dep = gini(F_1404['bal_end_r'].clip(lower=0).to_numpy())
gini_npl = gini(F_1404['npl_dec_r'].clip(lower=0).to_numpy())
print(f"\nGini Deposit: {gini_dep:.3f} (Claimed: 0.972)")
print(f"Gini NPL: {gini_npl:.3f} (Claimed: 0.995)")

# Save summary
y_summary = pd.DataFrame([
    {'task': 'Y1_total_deposit_hemat', 'reproduced': round(tot_dep, 2), 'claimed': 84.77},
    {'task': 'Y1_total_loan_hemat', 'reproduced': round(tot_loan, 2), 'claimed': 124.97},
    {'task': 'Y1_total_npl_hemat', 'reproduced': round(tot_npl, 2), 'claimed': 10.66},
    {'task': 'Y2_c1_dep_share', 'reproduced': round(c1_row['share_deposit']*100, 1), 'claimed': 60.8},
    {'task': 'Y2_c1_loan_share', 'reproduced': round(c1_row['share_loan']*100, 1), 'claimed': 51.4},
    {'task': 'Y2_c1_npl_share', 'reproduced': round(c1_row['share_npl']*100, 1), 'claimed': 37.5},
    {'task': 'Y2_t_loan_share', 'reproduced': round(t_row['share_loan']*100, 1), 'claimed': 8.7},
    {'task': 'Y2_t_npl_share', 'reproduced': round(t_row['share_npl']*100, 1), 'claimed': 30.1},
    {'task': 'Y2_t_npl_ratio', 'reproduced': round(t_row['npl_ratio']*100, 1), 'claimed': 29.7},
    {'task': 'Y2_c4_npl_share', 'reproduced': round(c4_row['share_npl']*100, 1), 'claimed': 10.1},
    {'task': 'Y2_c4_borrowers_count', 'reproduced': n_borr_c4, 'claimed': 1223},
    {'task': 'Y3_dep_top1pct_share', 'reproduced': round(s6_conc.loc[s6_conc['top_fraction']==0.01, 'deposit'].values[0]*100, 1), 'claimed': 78.7},
    {'task': 'Y3_dep_top10pct_share', 'reproduced': round(s6_conc.loc[s6_conc['top_fraction']==0.10, 'deposit'].values[0]*100, 1), 'claimed': 96.5},
    {'task': 'Y3_loan_top1pct_share', 'reproduced': round(s6_conc.loc[s6_conc['top_fraction']==0.01, 'loan_all_customers'].values[0]*100, 1), 'claimed': 62.2},
    {'task': 'Y3_loan_top10pct_share', 'reproduced': round(s6_conc.loc[s6_conc['top_fraction']==0.10, 'loan_all_customers'].values[0]*100, 1), 'claimed': 83.5},
    {'task': 'Y3_npl_top1pct_share', 'reproduced': round(s6_conc.loc[s6_conc['top_fraction']==0.01, 'npl_all_customers'].values[0]*100, 1), 'claimed': 93.6},
    {'task': 'Y3_gini_deposit', 'reproduced': round(gini_dep, 3), 'claimed': 0.972},
    {'task': 'Y3_gini_npl', 'reproduced': round(gini_npl, 3), 'claimed': 0.995},
    {'task': 'Y4_c1_cross_sell_count', 'reproduced': int(c1_x_row['eligible_100mt']), 'claimed': 10135},
    {'task': 'Y4_c1_cross_sell_dep_hemat', 'reproduced': round(c1_x_row['eligible_100mt_deposit_hemat'], 2), 'claimed': 28.13},
    {'task': 'Y5_c1_late30', 'reproduced': round(c1_row['late30']*100, 1), 'claimed': 15.2},
    {'task': 'Y5_c4_late30', 'reproduced': round(c4_row['late30']*100, 1), 'claimed': 47.3},
    {'task': 'Y5_c7_late30', 'reproduced': round(c7_row['late30']*100, 1), 'claimed': 52.3},
    {'task': 'Y5_t_late30', 'reproduced': round(t_row['late30']*100, 1), 'claimed': 59.8},
    {'task': 'Y6_c1_interest_index', 'reproduced': round(c1_row['interest_per_deposit']*100, 1), 'claimed': 7.7},
    {'task': 'Y6_s_interest_index', 'reproduced': round(s_row['interest_per_deposit']*100, 1), 'claimed': 9.8},
    {'task': 'Y6_c8_interest_index', 'reproduced': round(c8_row['interest_per_deposit']*100, 1), 'claimed': 1.5}
])
y_summary.to_csv(RESULTS / 'y01_to_y06_s6_reproduced.csv', index=False)
print("\nSaved Y1-Y6 summary to reports/review_S1_S10/results/y01_to_y06_s6_reproduced.csv")
