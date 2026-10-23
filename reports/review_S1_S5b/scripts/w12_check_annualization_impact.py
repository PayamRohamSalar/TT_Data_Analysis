import pandas as pd
from pathlib import Path
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

D = Path('data/processed/phase2_clustering')
F = pd.read_pickle(D / "features_customer_year.pkl")
pan = pd.read_pickle(D / "panel_customer_year.pkl")[["customer_id", "y", "bal_max"]]
F = F.merge(pan, on=["customer_id", "y"], how="left")
F["token_borrower"] = (F.category == "model") & F.has_primary_loan & ((F.turn_months < 3) | (F.bal_max < 5e6))
M = F[(F.category == "model") & ~F.token_borrower]
A = M[M.y == 1404].reset_index(drop=True)

print("A (1404 main) obs_months distribution:")
vc = A['obs_months'].value_counts().sort_index()
print(vc)
print(f"Total with obs_months < 12 in 1404 main: {(A['obs_months'] < 12).sum():,} out of {len(A):,} ({((A['obs_months'] < 12).mean()*100):.2f}%)")

# Compare across all years in M:
print("\nShare of obs_months < 12 in main population across years:")
for y, g in M.groupby('y'):
    sub12 = (g['obs_months'] < 12).sum()
    print(f"Year {y}: {sub12:,} / {len(g):,} ({sub12/len(g)*100:.2f}%)")
