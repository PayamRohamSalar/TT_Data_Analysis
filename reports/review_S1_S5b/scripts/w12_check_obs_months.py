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
print("Features columns:")
print([c for c in F.columns if 'month' in c or 'obs' in c])
print("'obs_months' in F.columns:", 'obs_months' in F.columns)
print("Distribution of obs_months if present:")
if 'obs_months' in F.columns:
    print(F['obs_months'].value_counts().sort_index())
