import pandas as pd
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

df = pd.read_csv('reports/review_S1_S5b/results/w04_churn_terminology_check.csv')
for f in ['reports\\phase2_S4_method_comparison.md', 'reports\\phase2_S5_final_model.md', 'reports\\phase2_S5b_lenses.md']:
    print(f"\n--- {f} ---")
    sub = df[df['file'] == f]
    for idx, r in sub.iterrows():
        print(f"Line {r['line']}: {r['text']}")
