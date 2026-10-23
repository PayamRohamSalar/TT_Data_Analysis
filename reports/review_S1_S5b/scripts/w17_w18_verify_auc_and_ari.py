import pandas as pd
from pathlib import Path
from sklearn.metrics import adjusted_rand_score
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

D = Path('data/processed/phase2_clustering')

print("--- W17: Inspecting kselect files for AUC ---")
cred_ks = pd.read_csv(D / "s5b_credit_lens_kselect.csv")
print("Credit Lens kselect:")
print(cred_ks[['k', 'half_ari', 'temporal_ari', 'min_share', 'auc_npl_entry', 'auc_late_next']].to_string())

dep_ks = pd.read_csv(D / "s5b_deposit_lens_kselect.csv")
print("\nDeposit Lens kselect:")
print(dep_ks[['k', 'half_ari', 'temporal_ari', 'min_share', 'auc_loan_uptake', 'auc_balance_halved', 'auc_lowactivity_next']].to_string())

# Verification of W18: ARI of lenses with main clusters
print("\n--- W18: Verifying ARI with main clusters ---")
ca = pd.read_pickle(D / "cluster_assignments_1404.pkl")
# Filter to main clusters (1..8)
ca_main = ca[ca['cluster'].isin(range(1, 9))]

# Deposit lens
dep_labels = pd.read_pickle(D / "deposit_lens_labels_1404.pkl")
merged_dep = ca_main.merge(dep_labels[['customer_id', 'deposit_lens']], on='customer_id')
ari_dep = adjusted_rand_score(merged_dep['cluster'], merged_dep['deposit_lens'])
print(f"Deposit Lens ARI with Main Clusters (N={len(merged_dep):,}): {ari_dep:.4f} (Claimed: 0.28)")

# Credit lens
cred_labels = pd.read_pickle(D / "credit_lens_labels_1404.pkl")
merged_cred = ca_main.merge(cred_labels[['customer_id', 'credit_lens']], on='customer_id')
ari_cred = adjusted_rand_score(merged_cred['cluster'], merged_cred['credit_lens'])
print(f"Credit Lens ARI with Main Clusters (N={len(merged_cred):,}): {ari_cred:.4f} (Claimed: 0.06)")

# Also check crosstabs
ct_dep = pd.read_csv(D / "s5b_deposit_lens_crosstab.csv")
ct_cred = pd.read_csv(D / "s5b_credit_lens_crosstab.csv")

print("\nDeposit Lens Crosstab with Main:")
print(ct_dep)

print("\nCredit Lens Crosstab with Main:")
print(ct_cred)

res_w17_w18 = pd.DataFrame([
    {'item': 'credit_lens_k5_auc_npl_entry', 'reproduced': cred_ks.loc[cred_ks['k']==5, 'auc_npl_entry'].values[0], 'claimed': 0.556},
    {'item': 'credit_lens_k5_auc_late_next', 'reproduced': cred_ks.loc[cred_ks['k']==5, 'auc_late_next'].values[0], 'claimed': 0.525},
    {'item': 'deposit_lens_k5_auc_lowactivity', 'reproduced': dep_ks.loc[dep_ks['k']==5, 'auc_lowactivity_next'].values[0], 'claimed': 0.772},
    {'item': 'deposit_lens_ari_with_main', 'reproduced': round(ari_dep, 2), 'claimed': 0.28},
    {'item': 'credit_lens_ari_with_main', 'reproduced': round(ari_cred, 2), 'claimed': 0.06}
])
res_w17_w18.to_csv('reports/review_S1_S5b/results/w17_w18_auc_and_ari_summary.csv', index=False)
print("Saved W17 and W18 summary.")
