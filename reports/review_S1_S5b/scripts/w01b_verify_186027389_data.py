import pandas as pd
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

df = pd.read_pickle('data/processed/phase2_clustering/customer_month_deposit.pkl')
sub = df[df['customer_id'] == 186027389]
print("Columns:", df.columns.tolist())
print("Last 5 rows for 186027389:")
print(sub.tail(5))
sub.to_csv('reports/review_S1_S5b/results/w01_customer_186027389_activity.csv', index=False)
