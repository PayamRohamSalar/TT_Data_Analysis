import pandas as pd
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

attrs = pd.read_pickle('data/processed/phase2_clustering/loan_contract_attrs.pkl')
print("Columns in loan_contract_attrs.pkl:", attrs.columns.tolist())
print("Shape:", attrs.shape)
print("Head:")
print(attrs.head(3))
