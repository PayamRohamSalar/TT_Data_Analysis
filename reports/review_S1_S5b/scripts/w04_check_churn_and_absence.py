import pandas as pd
import glob
import re
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Part 2: check absent customers from 1403 to 1404 in panel_customer_year.pkl
panel = pd.read_pickle('data/processed/phase2_clustering/panel_customer_year.pkl')
print("Panel shape:", panel.shape)
p1403 = panel[panel['y'] == 1403]
p1404 = panel[panel['y'] == 1404]

print("1403 categories:\n", p1403['category'].value_counts())
print("\n1404 categories:\n", p1404['category'].value_counts())

# Model customers of 1403
model_1403 = p1403[p1403['category'] == 'model']
n_model_1403 = len(model_1403)
cust_1403_model = set(model_1403['customer_id'])

# Check presence in 1404 (any category)
cust_1404_all = set(p1404['customer_id'])
absent_1404 = cust_1403_model - cust_1404_all

print(f"\nTotal model customers in 1403: {n_model_1403:,}")
print(f"Absent in 1404 (not in panel 1404 at all): {len(absent_1404):,}")

# Where did the remaining 1403 model customers go in 1404?
p1404_joined = p1404[p1404['customer_id'].isin(cust_1403_model)]
print("\nTransition of 1403 model customers in 1404:")
print(p1404_joined['category'].value_counts())

# Part 1: Text search for "خروج" or "کم‌فعال"
files_to_check = glob.glob('reports/phase2_*.md') + glob.glob('docs/phase2_*.md')
occurrences = []
for fpath in files_to_check:
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        for idx, line in enumerate(f, 1):
            if 'خروج' in line or 'کم‌فعال' in line:
                occurrences.append((fpath, idx, line.strip()))

out_df = pd.DataFrame(occurrences, columns=['file', 'line', 'text'])
out_df.to_csv('reports/review_S1_S5b/results/w04_churn_terminology_check.csv', index=False, encoding='utf-8-sig')
print(f"\nFound {len(occurrences)} lines mentioning churn/low-activity. Check saved to CSV.")
