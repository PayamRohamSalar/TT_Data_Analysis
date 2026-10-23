import pandas as pd
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

pan = pd.read_pickle('data/processed/phase2_clustering/panel_customer_year.pkl')
p1404 = pan[pan['y'] == 1404]

primary_contractual = p1404['bal_primary'].sum() / 1e13
inferred_primary = p1404['bal_inferred'].sum() / 1e13
total_attributed = primary_contractual + inferred_primary

print(f"Contractual Primary (with contract record): {primary_contractual:.4f} hemat")
print(f"Inferred Primary (single party, no contract record): {inferred_primary:.4f} hemat")
print(f"Total Attributed: {total_attributed:.4f} hemat")

# And total party balance (before attribution, repeating for every party):
bal_party_total = p1404['bal_party'].sum() / 1e13
print(f"Total Party Balance in panel: {bal_party_total:.4f} hemat")

# What about total in Loan_Remain 140412 in DB?
# Claimed: 128.2 hemat in bank/Loan_Remain
with open('reports/review_S1_S5b/results/w08_loan_attribution_totals.txt', 'w', encoding='utf-8') as f:
    f.write(f"Contractual Primary: {primary_contractual:.4f} hemat\n")
    f.write(f"Inferred Primary: {inferred_primary:.4f} hemat\n")
    f.write(f"Total Attributed: {total_attributed:.4f} hemat\n")
