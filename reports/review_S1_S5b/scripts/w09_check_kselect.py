import pandas as pd
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

df = pd.read_csv('data/processed/phase2_clustering/s5_kselect.csv')
print("--- s5_kselect.csv ---")
print(df.to_string())

df.to_csv('reports/review_S1_S5b/results/w09_s5_kselect_original.csv', index=False)
