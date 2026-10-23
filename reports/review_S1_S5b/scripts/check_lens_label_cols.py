import pandas as pd
from pathlib import Path

D = Path('data/processed/phase2_clustering')
c = pd.read_pickle(D / "credit_lens_labels_1404.pkl")
d = pd.read_pickle(D / "deposit_lens_labels_1404.pkl")

print("credit_lens_labels_1404 columns:", c.columns.tolist() if isinstance(c, pd.DataFrame) else type(c))
if isinstance(c, pd.DataFrame):
    print(c.head(2))
else:
    print("c shape:", getattr(c, 'shape', None))

print("deposit_lens_labels_1404 columns:", d.columns.tolist() if isinstance(d, pd.DataFrame) else type(d))
if isinstance(d, pd.DataFrame):
    print(d.head(2))
else:
    print("d shape:", getattr(d, 'shape', None))
