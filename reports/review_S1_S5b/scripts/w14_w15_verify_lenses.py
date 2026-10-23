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
print("Deposit columns:", dep.columns.tolist())
print(dep)
print("\nCredit columns:", cred.columns.tolist())
print(cred)
