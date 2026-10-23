import pandas as pd
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

cp = pd.read_csv('data/processed/phase2_clustering/cluster_profiles_1404.csv')
cols = ['segment', 'customers', 'share_customers', 'deposit_hemat', 'share_deposit', 
        'loan_hemat', 'share_loan', 'npl_hemat', 'npl_ratio']
print(cp[cols].to_string())

print("\n--- Summary Totals ---")
total_dep = cp['deposit_hemat'].sum()
total_loan = cp['loan_hemat'].sum()
total_npl = cp['npl_hemat'].sum()
print(f"Total Deposit: {total_dep:.2f} hemat")
print(f"Total Loan: {total_loan:.2f} hemat")
print(f"Total NPL: {total_npl:.2f} hemat")

cp.to_csv('reports/review_S1_S5b/results/w08_cluster_profiles_summary.csv', index=False)
