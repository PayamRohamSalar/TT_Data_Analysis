import json
from pathlib import Path
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

p = Path('data/processed/phase2_clustering/prep_spec_v2.json')
with open(p, 'r', encoding='utf-8') as f:
    d = json.load(f)

print("Top keys:", list(d.keys()))
print("ref_year:", d.get('ref_year'))
print("annualize:", d.get('annualize'))
print("\nKeys in mean (features):", list(d.get('mean', {}).keys()))
print(f"Number of features: {len(d.get('mean', {}))}")

print("\nSample feature parameters (bal_mean_r):")
for k in ['lo', 'hi', 'mean', 'std', 'weight']:
    print(f"  {k}: {d.get(k, {}).get('bal_mean_r')}")

# Check source code of Prep in src/tt_bank/phase2_clustering/prep.py
with open('src/tt_bank/phase2_clustering/prep.py', 'r', encoding='utf-8') as f:
    prep_code = f.read()

print("\n--- Inspecting fit and annualize in src/tt_bank/phase2_clustering/prep.py ---")
for line in prep_code.splitlines()[:60]:
    if 'def fit' in line or 'annualize' in line or 'months' in line or 'ref_year' in line:
        print(line)
