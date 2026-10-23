import pandas as pd
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

df = pd.read_csv('reports/review_S1_S5b/results/w04_churn_terminology_check.csv')
print("Total matches:", len(df))
print("\nFiles with occurrences:")
print(df['file'].value_counts())

print("\nSample lines with 'خروج':")
for idx, r in df[df['text'].str.contains('خروج')].head(10).iterrows():
    print(f"{r['file']}:{r['line']} -> {r['text'][:100]}")
