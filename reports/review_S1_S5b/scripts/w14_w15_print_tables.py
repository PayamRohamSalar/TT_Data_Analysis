import pandas as pd
from pathlib import Path
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

D = Path('data/processed/phase2_clustering')
dep = pd.read_csv(D / "s5b_deposit_lens_profile.csv")
cred = pd.read_csv(D / "s5b_credit_lens_profile.csv")

print("--- W14: Deposit Lens ---")
dep_summary = dep[['lens', 'customers', 'share_customers', 'deposit_share', 'loan_share']]
print(dep_summary.to_string())

print("\n--- W15: Credit Lens ---")
cred_summary = cred[['lens', 'borrowers', 'share_borrowers', 'loan_hemat', 'loan_share', 'npl_ratio', 'npl_share_of_total']]
print(cred_summary.to_string())

# Verification of sums:
c245_npl = cred.loc[cred['lens'].isin([2, 4, 5]), 'npl_share_of_total'].sum()
c245_borr = cred.loc[cred['lens'].isin([2, 4, 5]), 'share_borrowers'].sum()
print(f"\nSum of clusters 2, 4, 5 NPL share: {c245_npl*100:.2f}% (Claimed: 92.6%)")
print(f"Sum of clusters 2, 4, 5 Borrowers share: {c245_borr*100:.2f}% (Claimed: 26.2%)")

dep_summary.to_csv('reports/review_S1_S5b/results/w14_deposit_lens_table.csv', index=False)
cred_summary.to_csv('reports/review_S1_S5b/results/w15_credit_lens_table.csv', index=False)
